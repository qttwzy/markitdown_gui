import os
import json
import math
import logging
import pathlib
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple

from i18n import t

logger = logging.getLogger("markitdown_gui")

try:
    import fitz
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False

CATEGORY_DOCUMENT = "document"
CATEGORY_SPREADSHEET = "spreadsheet"
CATEGORY_PRESENTATION = "presentation"
CATEGORY_PDF = "pdf"
CATEGORY_IMAGE = "image"
CATEGORY_AUDIO = "audio"
CATEGORY_TEXT = "text"
CATEGORY_ARCHIVE = "archive"
CATEGORY_UNKNOWN = "unknown"

EXTENSION_CATEGORY: Dict[str, str] = {
    ".pdf": CATEGORY_PDF,
    ".docx": CATEGORY_DOCUMENT,
    ".doc": CATEGORY_DOCUMENT,
    ".pptx": CATEGORY_PRESENTATION,
    ".ppt": CATEGORY_PRESENTATION,
    ".xlsx": CATEGORY_SPREADSHEET,
    ".xls": CATEGORY_SPREADSHEET,
    ".csv": CATEGORY_SPREADSHEET,
    ".html": CATEGORY_TEXT,
    ".htm": CATEGORY_TEXT,
    ".xml": CATEGORY_TEXT,
    ".json": CATEGORY_TEXT,
    ".txt": CATEGORY_TEXT,
    ".md": CATEGORY_TEXT,
    ".rst": CATEGORY_TEXT,
    ".log": CATEGORY_TEXT,
    ".png": CATEGORY_IMAGE,
    ".jpg": CATEGORY_IMAGE,
    ".jpeg": CATEGORY_IMAGE,
    ".gif": CATEGORY_IMAGE,
    ".bmp": CATEGORY_IMAGE,
    ".tiff": CATEGORY_IMAGE,
    ".tif": CATEGORY_IMAGE,
    ".webp": CATEGORY_IMAGE,
    ".mp3": CATEGORY_AUDIO,
    ".wav": CATEGORY_AUDIO,
    ".ogg": CATEGORY_AUDIO,
    ".flac": CATEGORY_AUDIO,
    ".aac": CATEGORY_AUDIO,
    ".zip": CATEGORY_ARCHIVE,
}

CATEGORY_NAMES_KEYS: Dict[str, str] = {
    CATEGORY_DOCUMENT: "cat_document",
    CATEGORY_SPREADSHEET: "cat_spreadsheet",
    CATEGORY_PRESENTATION: "cat_presentation",
    CATEGORY_PDF: "cat_pdf",
    CATEGORY_IMAGE: "cat_image",
    CATEGORY_AUDIO: "cat_audio",
    CATEGORY_TEXT: "cat_text",
    CATEGORY_ARCHIVE: "cat_archive",
    CATEGORY_UNKNOWN: "cat_unknown",
}


def get_category_name(category: str) -> str:
    key = CATEGORY_NAMES_KEYS.get(category, "cat_unknown")
    return t(key)

BASE_RATES: Dict[str, float] = {
    CATEGORY_TEXT: 50_000_000,
    CATEGORY_DOCUMENT: 5_000_000,
    CATEGORY_SPREADSHEET: 3_000_000,
    CATEGORY_PRESENTATION: 3_000_000,
    CATEGORY_PDF: 200_000,
    CATEGORY_IMAGE: 15_000_000,
    CATEGORY_AUDIO: 8_000_000,
    CATEGORY_ARCHIVE: 2_000_000,
    CATEGORY_UNKNOWN: 3_000_000,
}

PDF_TIME_PER_PAGE = 0.15

SIZE_TIERS = [
    (100_000, 1.0),
    (1_000_000, 1.05),
    (5_000_000, 1.10),
    (10_000_000, 1.20),
    (50_000_000, 1.35),
    (100_000_000, 1.50),
    (500_000_000, 1.70),
    (float("inf"), 2.0),
]

MIN_PREDICTED_TIME = 0.01
CONFIDENCE_MARGIN = 0.15

CATEGORY_STARTUP: Dict[str, float] = {
    CATEGORY_TEXT: 0.005,
    CATEGORY_DOCUMENT: 0.02,
    CATEGORY_SPREADSHEET: 0.02,
    CATEGORY_PRESENTATION: 0.02,
    CATEGORY_PDF: 0.01,
    CATEGORY_IMAGE: 0.01,
    CATEGORY_AUDIO: 0.01,
    CATEGORY_ARCHIVE: 0.02,
    CATEGORY_UNKNOWN: 0.02,
}

CATEGORY_MIN_TIME: Dict[str, float] = {
    CATEGORY_TEXT: 0.01,
    CATEGORY_DOCUMENT: 0.05,
    CATEGORY_SPREADSHEET: 0.05,
    CATEGORY_PRESENTATION: 0.05,
    CATEGORY_PDF: 0.02,
    CATEGORY_IMAGE: 0.02,
    CATEGORY_AUDIO: 0.02,
    CATEGORY_ARCHIVE: 0.05,
    CATEGORY_UNKNOWN: 0.05,
}


@dataclass
class PredictionResult:
    predicted_seconds: float
    lower_bound: float
    upper_bound: float
    category: str
    category_name: str
    file_size: int
    rate_used: float
    confidence: str
    is_range: bool

    @property
    def predicted_display(self) -> str:
        return self._format_time(self.predicted_seconds)

    @property
    def lower_display(self) -> str:
        return self._format_time(self.lower_bound)

    @property
    def upper_display(self) -> str:
        return self._format_time(self.upper_bound)

    @property
    def range_display(self) -> str:
        return f"{self.lower_display} ~ {self.upper_display}"

    @staticmethod
    def _format_time(seconds: float) -> str:
        if seconds < 0.01:
            return "<0.01s"
        if seconds < 1:
            return f"{seconds:.2f}s"
        if seconds < 60:
            return f"{seconds:.1f}s"
        mins = int(seconds) // 60
        secs = seconds - mins * 60
        return f"{mins}m {secs:.0f}s"


@dataclass
class HistorySample:
    category: str
    file_size: int
    duration: float
    page_count: Optional[int] = None


class ConversionPredictor:
    def __init__(self, model_file: Optional[str] = None):
        self._model_file = model_file or os.path.join(
            os.path.expanduser("~"), ".markitdown_gui_predictor.json"
        )
        self._rates: Dict[str, float] = dict(BASE_RATES)
        self._history_samples: Dict[str, List[HistorySample]] = {}
        self._category_counts: Dict[str, int] = {}
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self._model_file):
                with open(self._model_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "rates" in data:
                    for k, v in data["rates"].items():
                        self._rates[k] = v
                if "samples" in data:
                    for cat, items in data["samples"].items():
                        self._history_samples[cat] = [
                            HistorySample(**s) for s in items
                        ]
                if "counts" in data:
                    self._category_counts = data["counts"]
                logger.info(
                    t("log_predictor_loaded", categories=len(self._rates),
                      samples=sum(len(v) for v in self._history_samples.values()))
                )
        except (json.JSONDecodeError, OSError, TypeError) as e:
            logger.warning(t("log_predictor_load_failed", error=e))

    def _save_model(self):
        try:
            data = {
                "rates": self._rates,
                "samples": {
                    cat: [asdict(s) for s in samples]
                    for cat, samples in self._history_samples.items()
                },
                "counts": self._category_counts,
            }
            with open(self._model_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(t("log_predictor_save_failed", error=e))

    @staticmethod
    def classify_file(file_path: str) -> str:
        ext = pathlib.Path(file_path).suffix.lower()
        return EXTENSION_CATEGORY.get(ext, CATEGORY_UNKNOWN)

    @staticmethod
    def classify_extension(ext: str) -> str:
        ext = ext.lower()
        if not ext.startswith("."):
            ext = "." + ext
        return EXTENSION_CATEGORY.get(ext, CATEGORY_UNKNOWN)

    def predict(self, file_path: str, file_size: Optional[int] = None) -> PredictionResult:
        category = self.classify_file(file_path)

        if file_size is None:
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                file_size = 0

        if category == CATEGORY_PDF:
            predicted = self._predict_pdf(file_path, file_size)
        else:
            rate = self._get_effective_rate(category, file_size)
            size_factor = self._get_size_factor(file_size)
            startup = CATEGORY_STARTUP.get(category, CATEGORY_STARTUP[CATEGORY_UNKNOWN])
            min_time = CATEGORY_MIN_TIME.get(category, CATEGORY_MIN_TIME[CATEGORY_UNKNOWN])
            raw_time = (file_size / rate) * size_factor + startup
            predicted = max(raw_time, min_time)

        confidence = self._compute_confidence(category, file_size)
        margin = CONFIDENCE_MARGIN
        if confidence == "low":
            margin = 0.30
        elif confidence == "medium":
            margin = 0.20

        lower = max(predicted * (1 - margin), MIN_PREDICTED_TIME)
        upper = predicted * (1 + margin)

        is_range = confidence == "low" or category == CATEGORY_UNKNOWN

        rate_used = self._get_effective_rate(category, file_size)

        return PredictionResult(
            predicted_seconds=round(predicted, 2),
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            category=category,
            category_name=get_category_name(category),
            file_size=file_size,
            rate_used=rate_used,
            confidence=confidence,
            is_range=is_range,
        )

    def _predict_pdf(self, file_path: str, file_size: int) -> float:
        page_count = self._get_pdf_page_count(file_path)
        startup = CATEGORY_STARTUP.get(CATEGORY_PDF, 0.01)
        min_time = CATEGORY_MIN_TIME.get(CATEGORY_PDF, 0.02)

        if page_count and page_count > 0:
            time_per_page = self._get_pdf_time_per_page()
            io_rate = self._get_effective_rate(CATEGORY_PDF, file_size)
            page_component = page_count * time_per_page
            io_component = file_size / io_rate if io_rate > 0 else 0
            predicted = startup + page_component + io_component
            logger.debug(
                t("log_pdf_predict", pages=page_count,
                  time_per_page=f"{time_per_page:.3f}",
                  io=f"{io_component:.3f}", predicted=f"{predicted:.2f}")
            )
            return max(predicted, min_time)

        rate = self._get_effective_rate(CATEGORY_PDF, file_size)
        size_factor = self._get_size_factor(file_size)
        raw_time = (file_size / rate) * size_factor + startup
        return max(raw_time, min_time)

    @staticmethod
    def _get_pdf_page_count(file_path: str) -> Optional[int]:
        if not _PYMUPDF_AVAILABLE:
            return None
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return None

    def _get_pdf_time_per_page(self) -> float:
        samples = self._history_samples.get(CATEGORY_PDF, [])
        if len(samples) >= 2:
            recent = samples[-20:]
            page_times = []
            for s in recent:
                if s.duration > 0.1:
                    pages = s.page_count if s.page_count and s.page_count > 0 else max(1, s.file_size / 50_000)
                    page_times.append(s.duration / pages)
            if page_times:
                return sum(page_times) / len(page_times)
        return PDF_TIME_PER_PAGE

    def predict_batch(self, file_paths: List[str]) -> Tuple[float, float, float]:
        total_predicted = 0.0
        total_lower = 0.0
        total_upper = 0.0
        for fp in file_paths:
            pred = self.predict(fp)
            total_predicted += pred.predicted_seconds
            total_lower += pred.lower_bound
            total_upper += pred.upper_bound
        return (
            round(total_predicted, 2),
            round(total_lower, 2),
            round(total_upper, 2),
        )

    def record_actual(self, file_path: str, file_size: int, duration: float):
        if duration <= 0 or file_size <= 0:
            return

        category = self.classify_file(file_path)
        page_count = None
        if category == CATEGORY_PDF:
            page_count = self._get_pdf_page_count(file_path)

        sample = HistorySample(
            category=category, file_size=file_size, duration=duration,
            page_count=page_count,
        )

        if category not in self._history_samples:
            self._history_samples[category] = []
        self._history_samples[category].append(sample)

        if len(self._history_samples[category]) > 200:
            self._history_samples[category] = self._history_samples[category][-200:]

        self._category_counts[category] = self._category_counts.get(category, 0) + 1

        self._recalibrate_rate(category)
        self._save_model()

        logger.debug(
            t("log_sample_recorded", category=category,
              size=file_size, duration=f"{duration:.2f}")
        )

    def _get_effective_rate(self, category: str, file_size: int) -> float:
        base = self._rates.get(category, self._rates[CATEGORY_UNKNOWN])
        samples = self._history_samples.get(category, [])

        if len(samples) < 5:
            return base

        startup = CATEGORY_STARTUP.get(category, CATEGORY_STARTUP[CATEGORY_UNKNOWN])
        recent = samples[-30:]
        weighted_rate = 0.0
        weight_sum = 0.0

        for i, s in enumerate(recent):
            if s.duration > 0.05 and s.file_size > 0:
                processing_time = max(s.duration - startup, 0.001)
                sample_rate = s.file_size / processing_time
                w = (i + 1) / len(recent)
                weighted_rate += sample_rate * w
                weight_sum += w

        if weight_sum > 0:
            empirical_rate = weighted_rate / weight_sum
            n = len(samples)
            alpha = min(n / 40, 0.6)
            return base * (1 - alpha) + empirical_rate * alpha

        return base

    @staticmethod
    def _get_size_factor(file_size: int) -> float:
        for threshold, factor in SIZE_TIERS:
            if file_size < threshold:
                return factor
        return SIZE_TIERS[-1][1]

    def _compute_confidence(self, category: str, file_size: int) -> str:
        count = self._category_counts.get(category, 0)
        samples = self._history_samples.get(category, [])

        if category == CATEGORY_UNKNOWN:
            return "low"

        if count < 3:
            return "low"

        if category == CATEGORY_PDF:
            return self._compute_pdf_confidence(file_size, samples)

        if count < 10:
            return "medium"

        if not samples:
            return "medium"

        recent = samples[-20:]
        rates = []
        for s in recent:
            if s.duration > 0 and s.file_size > 0:
                rates.append(s.file_size / s.duration)

        if len(rates) < 3:
            return "medium"

        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        cv = math.sqrt(variance) / mean_rate if mean_rate > 0 else 1.0

        if cv > 0.5:
            return "medium"

        max_sample_size = max(s.file_size for s in recent)
        if file_size > max_sample_size * 5:
            return "medium"

        return "high"

    @staticmethod
    def _compute_pdf_confidence(file_size: int, samples: List[HistorySample]) -> str:
        if len(samples) < 5:
            return "low"

        recent = samples[-20:]
        page_counts = [s.page_count for s in recent if s.page_count and s.page_count > 0]

        if not page_counts:
            return "low"

        avg_pages = sum(page_counts) / len(page_counts)
        max_pages = max(page_counts)

        if file_size > max(s.file_size for s in recent) * 3:
            return "low"

        if max_pages > 0 and file_size / max_pages > avg_pages * 3:
            return "low"

        if len(samples) < 10:
            return "medium"

        return "medium"

    def _recalibrate_rate(self, category: str):
        samples = self._history_samples.get(category, [])
        if len(samples) < 3:
            return

        startup = CATEGORY_STARTUP.get(category, CATEGORY_STARTUP[CATEGORY_UNKNOWN])
        recent = samples[-30:]
        rates = []
        for s in recent:
            if s.duration > 0 and s.file_size > 0:
                processing_time = max(s.duration - startup, 0.001)
                rates.append(s.file_size / processing_time)

        if not rates:
            return

        empirical_rate = sum(rates) / len(rates)
        base = BASE_RATES.get(category, BASE_RATES[CATEGORY_UNKNOWN])
        n = len(samples)
        alpha = min(n / 20, 0.85)
        self._rates[category] = base * (1 - alpha) + empirical_rate * alpha
        logger.debug(
            t("log_rate_calibrated", category=category,
              base=f"{base / 1_000_000:.1f}", new_rate=f"{self._rates[category] / 1_000_000:.1f}",
              alpha=f"{alpha:.2f}", samples=n)
        )

    def get_model_stats(self) -> Dict[str, Dict]:
        stats = {}
        for cat in self._rates:
            samples = self._history_samples.get(cat, [])
            count = self._category_counts.get(cat, 0)
            rate = self._rates.get(cat, 0)
            stats[cat] = {
                "name": get_category_name(cat),
                "rate": rate,
                "samples": count,
                "display_rate": f"{rate / 1_000_000:.1f} MB/s",
            }
        return stats
