from __future__ import annotations

import logging

from instant_translator.utils.paths import get_default_log_path


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("instant_translator")
    if logger.handlers:
        return logger

    log_path = get_default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
