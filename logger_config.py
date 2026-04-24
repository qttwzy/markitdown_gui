import os
import logging
from datetime import datetime

from i18n import t


def setup_logging() -> logging.Logger:
    log_dir = os.path.join(os.path.expanduser("~"), ".markitdown_gui")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger = logging.getLogger("markitdown_gui")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_fmt = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(t("log_logging_initialized"))
    logger.info(t("log_log_file", path=log_file))

    return logger
