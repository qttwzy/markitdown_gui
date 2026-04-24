import os
import json
import logging
from typing import Dict

logger = logging.getLogger("markitdown_gui")

LANG_ZH = "zh"
LANG_EN = "en"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    LANG_ZH: {
        "app_title": "MarkItDown - 文件转换工具",
        "title_label": "MarkItDown 文件转换工具",
        "drop_text": "拖拽文件到此处，或点击下方按钮选择文件",
        "drop_sub": "支持 PDF、Word、Excel、PPT、HTML、图片、音频等格式",
        "path_label": "文件路径:",
        "add_btn": "添加",
        "file_list_frame": " 待转换文件列表 ",
        "col_index": "#",
        "col_filename": "文件名",
        "col_size": "大小",
        "col_predicted": "预估耗时",
        "col_path": "完整路径",
        "count_files": "共 {count} 个文件",
        "total_size": "总大小: {size}",
        "remove_selected": "移除选中",
        "clear_list": "清空列表",
        "prediction_frame": " 智能预测 ",
        "pred_total": "预计总耗时: {time}",
        "pred_total_none": "预计总耗时: --",
        "pred_range": "区间: {lower} ~ {upper}",
        "confidence_high": "置信度: 高",
        "confidence_medium": "置信度: 中",
        "confidence_low": "置信度: 低",
        "file_composition": "文件构成: {parts}",
        "status_ready": "准备转换",
        "status_converting": "转换进行中",
        "status_success": "转换成功完成",
        "status_failed": "转换失败",
        "start_btn": "▶  开 始",
        "stop_btn": "■  停 止",
        "browse_btn": "📂  浏览文件",
        "history_frame": " 转换历史 ",
        "col_time": "时间",
        "col_source": "源文件",
        "col_status": "状态",
        "col_duration": "实际耗时",
        "col_pred_time": "预测耗时",
        "col_error": "错误信息",
        "refresh_history": "刷新历史",
        "clear_history": "清空历史",
        "status_success_short": "成功",
        "status_failed_short": "失败",
        "status_empty_short": "空结果",
        "confirm_clear_list": "确定要清空文件列表吗？",
        "confirm_clear_history": "确定要清空所有转换历史记录吗？",
        "confirm_title": "确认",
        "confirm_convert_title": "确认转换",
        "confirm_convert_msg": "即将转换 {count} 个文件\n预计耗时: {pred} ({lower} ~ {upper})\n是否继续？",
        "warning_no_files": "请先添加要转换的文件",
        "warning_title": "提示",
        "skip_invalid": "跳过无效文件: {path}\n  原因: {reason}",
        "path_not_exist": "路径不存在: {path}",
        "added_files": "已添加 {count} 个文件",
        "invalid_file": "无效文件: {path}\n  原因: {reason}",
        "duplicate_file": "文件已在列表中: {path}",
        "list_cleared": "文件列表已清空",
        "history_cleared": "历史记录已清空",
        "stopping": "正在停止转换...",
        "stopped": "转换已被用户中止",
        "converting_item": "[{current}/{total}] 正在转换: {name} (预估: {pred})",
        "convert_success": "[{current}/{total}] ✓ 转换成功: {name}\n  输出: {output} (实际: {actual}s, 预测: {pred}{error})",
        "convert_failed": "[{current}/{total}] ✗ 转换失败: {name}\n  错误: {error}",
        "error_pct": " [误差: {pct}%]",
        "all_done": "\n全部转换完成！成功: {count}",
        "partial_done": "\n转换完成（部分失败）- 成功: {success}, 失败: {fail}",
        "all_failed": "\n转换失败 - 失败: {count}",
        "pred_total_detail": "预测总耗时: {pred} ({lower} ~ {upper})",
        "browse_title": "选择要转换的文件",
        "filter_all_supported": "所有支持的格式",
        "filter_pdf": "PDF 文件",
        "filter_word": "Word 文档",
        "filter_ppt": "PowerPoint 演示文稿",
        "filter_excel": "Excel 工作簿",
        "filter_html": "HTML 文件",
        "filter_text": "文本文件",
        "filter_image": "图片文件",
        "filter_audio": "音频文件",
        "filter_all": "所有文件",
        "language_menu": "语言/Language",
        "lang_zh": "中文",
        "lang_en": "English",
        "cat_document": "文档",
        "cat_spreadsheet": "表格",
        "cat_presentation": "演示文稿",
        "cat_pdf": "PDF",
        "cat_image": "图片",
        "cat_audio": "音频",
        "cat_text": "文本",
        "cat_archive": "压缩包",
        "cat_unknown": "未知",
        "err_empty_path": "文件路径为空",
        "err_not_exist": "文件不存在: {path}",
        "err_is_dir": "路径是目录而非文件: {path}",
        "err_not_file": "无法识别的文件类型: {path}",
        "err_unsupported_format": "不支持的文件格式 '{ext}'，支持的格式: {supported}",
        "err_no_read_perm": "文件无读取权限: {path}",
        "err_no_write_perm": "无写入权限: {path}",
        "err_write_failed": "写入文件失败: {path} - {error}",
        "err_permission_denied": "权限不足，无法读取或写入文件: {path}",
        "err_filesystem": "文件系统错误: {error}",
        "err_conversion_failed": "转换失败: {type}: {error}",
        "err_empty_result": "转换结果为空: {path}",
        "log_path_normalize_failed": "路径标准化失败: {path} -> {error}",
        "log_history_loaded": "已加载 {count} 条历史记录",
        "log_history_load_failed": "加载历史记录失败: {error}",
        "log_history_save_failed": "保存历史记录失败: {error}",
        "log_start_conversion": "开始转换: {path} (大小: {size})",
        "log_pdf_fallback": "markitdown PDF 转换结果为空，尝试 PyMuPDF 增强转换: {path}",
        "log_pdf_fallback_success": "PyMuPDF 增强转换成功: {path}",
        "log_conversion_success": "转换成功: {path} -> {output} (耗时: {duration}s)",
        "log_pymupdf_not_installed": "PyMuPDF 未安装，无法使用增强 PDF 转换",
        "log_pymupdf_fallback_failed": "PyMuPDF 增强转换失败: {error}",
        "log_large_file_mode": "大文件模式转换: {path}",
        "log_predictor_loaded": "预测模型已加载: {categories} 类别, {samples} 样本",
        "log_predictor_load_failed": "加载预测模型失败: {error}",
        "log_predictor_save_failed": "保存预测模型失败: {error}",
        "log_rate_calibrated": "速率校准: {category} base={base}MB/s -> new={new_rate}MB/s (alpha={alpha}, samples={samples})",
        "log_sample_recorded": "记录转换样本: {category} {size}B {duration}s",
        "log_pdf_predict": "PDF预测: {pages}页 × {time_per_page}s/页 + I/O {io}s = {predicted}s",
        "log_logging_initialized": "日志系统初始化完成",
        "log_log_file": "日志文件: {path}",
    },
    LANG_EN: {
        "app_title": "MarkItDown - File Converter",
        "title_label": "MarkItDown File Converter",
        "drop_text": "Drag & drop files here, or click the button below",
        "drop_sub": "Supports PDF, Word, Excel, PPT, HTML, Images, Audio and more",
        "path_label": "File Path:",
        "add_btn": "Add",
        "file_list_frame": " File Queue ",
        "col_index": "#",
        "col_filename": "Filename",
        "col_size": "Size",
        "col_predicted": "Est. Time",
        "col_path": "Full Path",
        "count_files": "{count} file(s)",
        "total_size": "Total: {size}",
        "remove_selected": "Remove",
        "clear_list": "Clear All",
        "prediction_frame": " Smart Prediction ",
        "pred_total": "Est. Total: {time}",
        "pred_total_none": "Est. Total: --",
        "pred_range": "Range: {lower} ~ {upper}",
        "confidence_high": "Confidence: High",
        "confidence_medium": "Confidence: Medium",
        "confidence_low": "Confidence: Low",
        "file_composition": "Composition: {parts}",
        "status_ready": "Ready",
        "status_converting": "Converting...",
        "status_success": "Conversion Complete",
        "status_failed": "Conversion Failed",
        "start_btn": "▶  START",
        "stop_btn": "■  STOP",
        "browse_btn": "📂  Browse",
        "history_frame": " Conversion History ",
        "col_time": "Time",
        "col_source": "Source",
        "col_status": "Status",
        "col_duration": "Actual",
        "col_pred_time": "Predicted",
        "col_error": "Error",
        "refresh_history": "Refresh",
        "clear_history": "Clear",
        "status_success_short": "Success",
        "status_failed_short": "Failed",
        "status_empty_short": "Empty",
        "confirm_clear_list": "Are you sure you want to clear the file list?",
        "confirm_clear_history": "Are you sure you want to clear all conversion history?",
        "confirm_title": "Confirm",
        "confirm_convert_title": "Confirm Conversion",
        "confirm_convert_msg": "Convert {count} file(s)?\nEstimated time: {pred} ({lower} ~ {upper})\nContinue?",
        "warning_no_files": "Please add files first",
        "warning_title": "Notice",
        "skip_invalid": "Skipped invalid file: {path}\n  Reason: {reason}",
        "path_not_exist": "Path not found: {path}",
        "added_files": "Added {count} file(s)",
        "invalid_file": "Invalid file: {path}\n  Reason: {reason}",
        "duplicate_file": "File already in list: {path}",
        "list_cleared": "File list cleared",
        "history_cleared": "History cleared",
        "stopping": "Stopping conversion...",
        "stopped": "Conversion stopped by user",
        "converting_item": "[{current}/{total}] Converting: {name} (est: {pred})",
        "convert_success": "[{current}/{total}] ✓ Success: {name}\n  Output: {output} (actual: {actual}s, predicted: {pred}{error})",
        "convert_failed": "[{current}/{total}] ✗ Failed: {name}\n  Error: {error}",
        "error_pct": " [error: {pct}%]",
        "all_done": "\nAll done! Success: {count}",
        "partial_done": "\nCompleted (partial) - Success: {success}, Failed: {fail}",
        "all_failed": "\nConversion failed - Failed: {count}",
        "pred_total_detail": "Estimated total: {pred} ({lower} ~ {upper})",
        "browse_title": "Select files to convert",
        "filter_all_supported": "All Supported Formats",
        "filter_pdf": "PDF Files",
        "filter_word": "Word Documents",
        "filter_ppt": "PowerPoint Presentations",
        "filter_excel": "Excel Workbooks",
        "filter_html": "HTML Files",
        "filter_text": "Text Files",
        "filter_image": "Image Files",
        "filter_audio": "Audio Files",
        "filter_all": "All Files",
        "language_menu": "语言/Language",
        "lang_zh": "中文",
        "lang_en": "English",
        "cat_document": "Document",
        "cat_spreadsheet": "Spreadsheet",
        "cat_presentation": "Presentation",
        "cat_pdf": "PDF",
        "cat_image": "Image",
        "cat_audio": "Audio",
        "cat_text": "Text",
        "cat_archive": "Archive",
        "cat_unknown": "Unknown",
        "err_empty_path": "File path is empty",
        "err_not_exist": "File not found: {path}",
        "err_is_dir": "Path is a directory, not a file: {path}",
        "err_not_file": "Unrecognized file type: {path}",
        "err_unsupported_format": "Unsupported format '{ext}', supported: {supported}",
        "err_no_read_perm": "No read permission: {path}",
        "err_no_write_perm": "No write permission: {path}",
        "err_write_failed": "Failed to write file: {path} - {error}",
        "err_permission_denied": "Permission denied, cannot read or write: {path}",
        "err_filesystem": "Filesystem error: {error}",
        "err_conversion_failed": "Conversion failed: {type}: {error}",
        "err_empty_result": "Conversion result is empty: {path}",
        "log_path_normalize_failed": "Path normalization failed: {path} -> {error}",
        "log_history_loaded": "Loaded {count} history record(s)",
        "log_history_load_failed": "Failed to load history: {error}",
        "log_history_save_failed": "Failed to save history: {error}",
        "log_start_conversion": "Starting conversion: {path} (size: {size})",
        "log_pdf_fallback": "markitdown PDF result empty, trying PyMuPDF fallback: {path}",
        "log_pdf_fallback_success": "PyMuPDF fallback succeeded: {path}",
        "log_conversion_success": "Conversion succeeded: {path} -> {output} (duration: {duration}s)",
        "log_pymupdf_not_installed": "PyMuPDF not installed, PDF fallback unavailable",
        "log_pymupdf_fallback_failed": "PyMuPDF fallback failed: {error}",
        "log_large_file_mode": "Large file mode conversion: {path}",
        "log_predictor_loaded": "Prediction model loaded: {categories} categories, {samples} samples",
        "log_predictor_load_failed": "Failed to load prediction model: {error}",
        "log_predictor_save_failed": "Failed to save prediction model: {error}",
        "log_rate_calibrated": "Rate calibrated: {category} base={base}MB/s -> new={new_rate}MB/s (alpha={alpha}, samples={samples})",
        "log_sample_recorded": "Sample recorded: {category} {size}B {duration}s",
        "log_pdf_predict": "PDF prediction: {pages} pages × {time_per_page}s/page + I/O {io}s = {predicted}s",
        "log_logging_initialized": "Logging system initialized",
        "log_log_file": "Log file: {path}",
    },
}

_current_lang = LANG_ZH
_config_path = os.path.join(os.path.expanduser("~"), ".markitdown_gui_lang.json")


def get_lang() -> str:
    return _current_lang


def set_lang(lang: str):
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang
        _save_lang_pref(lang)


def load_lang_pref():
    global _current_lang
    try:
        if os.path.exists(_config_path):
            with open(_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lang = data.get("language", LANG_ZH)
            if lang in TRANSLATIONS:
                _current_lang = lang
    except Exception:
        pass


def _save_lang_pref(lang: str):
    try:
        with open(_config_path, "w", encoding="utf-8") as f:
            json.dump({"language": lang}, f)
    except Exception:
        pass


def t(key: str, **kwargs) -> str:
    translations = TRANSLATIONS.get(_current_lang, TRANSLATIONS[LANG_ZH])
    template = translations.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


load_lang_pref()
