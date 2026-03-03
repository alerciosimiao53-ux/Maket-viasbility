import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "smart_market_intelligence", level: str = "INFO") -> logging.Logger:
    """Create and configure project logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    os.makedirs("smart_market_intelligence/reports", exist_ok=True)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        "smart_market_intelligence/reports/system.log", maxBytes=500_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
