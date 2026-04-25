import os
import re
import json
import time
import logging
import pathlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List

from markitdown import MarkItDown

from i18n import t

LARGE_FILE_THRESHOLD = 10 * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
    ".html", ".htm", ".csv", ".json", ".xml",
    ".txt", ".md", ".rst", ".log",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    ".mp3", ".wav", ".ogg", ".flac", ".aac",
    ".zip",
}

logger = logging.getLogger("markitdown_gui")


@dataclass
class ConversionRecord:
    source_path: str
    output_path: Optional[str]
    status: str
    timestamp: str
    error: Optional[str] = None
    file_size: int = 0
    duration: float = 0.0


@dataclass
class ConversionResult:
    success: bool
    source_path: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    file_size: int = 0


def normalize_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    cleaned = raw_path.strip().strip('"').strip("'")
    cleaned = re.sub(r'[/\\]+', re.escape(os.sep), cleaned)
    try:
        resolved = pathlib.Path(cleaned).resolve()
        return str(resolved)
    except (OSError, ValueError) as e:
        logger.warning(t("log_path_normalize_failed", path=raw_path, error=e))
        return cleaned


def validate_file(file_path: str) -> tuple[bool, str]:
    if not file_path:
        return False, t("err_empty_path")
    norm = normalize_path(file_path)
    if not os.path.exists(norm):
        return False, t("err_not_exist", path=norm)
    if os.path.isdir(norm):
        return False, t("err_is_dir", path=norm)
    if not os.path.isfile(norm):
        return False, t("err_not_file", path=norm)
    ext = pathlib.Path(norm).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return False, t("err_unsupported_format", ext=ext, supported=supported)
    if not os.access(norm, os.R_OK):
        return False, t("err_no_read_perm", path=norm)
    return True, ""


class ConversionEngine:
    def __init__(self, history_file: Optional[str] = None):
        self._md = MarkItDown()
        self._history: List[ConversionRecord] = []
        self._history_file = history_file or os.path.join(
            os.path.expanduser("~"), ".markitdown_gui_history.json"
        )
        self._load_history()

    def _load_history(self):
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._history = [ConversionRecord(**item) for item in data]
                logger.info(t("log_history_loaded", count=len(self._history)))
        except (json.JSONDecodeError, OSError, TypeError) as e:
            logger.warning(t("log_history_load_failed", error=e))
            self._history = []

    def _save_history(self):
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self._history], f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(t("log_history_save_failed", error=e))

    def get_history(self) -> List[ConversionRecord]:
        return list(self._history)

    def clear_history(self):
        self._history.clear()
        self._save_history()

    def convert_file(self, file_path: str) -> ConversionResult:
        norm_path = normalize_path(file_path)
        valid, err = validate_file(norm_path)
        if not valid:
            logger.error(f"Validation failed: {err}")
            return ConversionResult(
                success=False, source_path=norm_path, error=err
            )

        file_size = os.path.getsize(norm_path)
        start_mono = time.monotonic()
        start_time = datetime.now()
        logger.info(t("log_start_conversion", path=norm_path, size=self._fmt_size(file_size)))

        try:
            if file_size > LARGE_FILE_THRESHOLD:
                result = self._convert_large_file(norm_path)
            else:
                result = self._md.convert_local(norm_path)

            duration = time.monotonic() - start_mono
            markdown_content = result.markdown

            if not markdown_content or not markdown_content.strip():
                error_msg = t("err_empty_result", path=norm_path)
                logger.warning(error_msg)
                record = ConversionRecord(
                    source_path=norm_path, output_path=None,
                    status="empty", timestamp=start_time.isoformat(),
                    error=error_msg, file_size=file_size, duration=duration,
                )
                self._history.append(record)
                self._save_history()
                return ConversionResult(
                    success=False, source_path=norm_path,
                    error=error_msg, duration=duration, file_size=file_size,
                )

            output_path = self._get_output_path(norm_path)
            self._write_output(output_path, markdown_content)

            record = ConversionRecord(
                source_path=norm_path, output_path=output_path,
                status="success", timestamp=start_time.isoformat(),
                file_size=file_size, duration=duration,
            )
            self._history.append(record)
            self._save_history()

            logger.info(
                t("log_conversion_success", path=norm_path, output=output_path,
                  duration=f"{duration:.2f}")
            )
            return ConversionResult(
                success=True, source_path=norm_path,
                output_path=output_path, duration=duration,
                file_size=file_size,
            )

        except PermissionError:
            error_msg = t("err_permission_denied", path=norm_path)
            logger.error(error_msg)
            return self._record_failure(norm_path, file_size, start_time, error_msg, start_mono)
        except OSError as e:
            error_msg = t("err_filesystem", error=e)
            logger.error(error_msg)
            return self._record_failure(norm_path, file_size, start_time, error_msg, start_mono)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"{t('err_conversion_failed', type=type(e).__name__, error=e)}\n{tb}")
            return self._record_failure(norm_path, file_size, start_time, error_msg, start_mono)

    def _convert_large_file(self, file_path: str):
        logger.info(t("log_large_file_mode", path=file_path))
        return self._md.convert_local(file_path)

    def _get_output_path(self, source_path: str) -> str:
        p = pathlib.Path(source_path)
        output_name = p.stem + ".md"
        output_path = p.parent / output_name
        counter = 1
        while output_path.exists():
            output_name = f"{p.stem}_{counter}.md"
            output_path = p.parent / output_name
            counter += 1
        return str(output_path)

    def _write_output(self, output_path: str, content: str):
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        except PermissionError:
            raise PermissionError(t("err_no_write_perm", path=output_path))
        except OSError as e:
            raise OSError(t("err_write_failed", path=output_path, error=e))

    def _record_failure(
        self, source_path: str, file_size: int,
        start_time: datetime, error_msg: str,
        start_mono: Optional[float] = None,
    ) -> ConversionResult:
        if start_mono is not None:
            duration = time.monotonic() - start_mono
        else:
            duration = (datetime.now() - start_time).total_seconds()
        record = ConversionRecord(
            source_path=source_path, output_path=None,
            status="failed", timestamp=start_time.isoformat(),
            error=error_msg, file_size=file_size, duration=duration,
        )
        self._history.append(record)
        self._save_history()
        return ConversionResult(
            success=False, source_path=source_path,
            error=error_msg, duration=duration, file_size=file_size,
        )

    @staticmethod
    def _fmt_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
