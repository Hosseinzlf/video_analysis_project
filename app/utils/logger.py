import logging
import sys
from pathlib import Path


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )

    # File
    Path("logs").mkdir(exist_ok=True)
    file_handler = logging.FileHandler(Path("logs") / f"{name}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger