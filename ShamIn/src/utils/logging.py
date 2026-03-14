"""ShamIn logging setup."""
import logging
import sys
from pathlib import Path


_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def setup_logger(name: str = "shamin", level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Create and configure a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler
    if log_file:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(_LOG_DIR / log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# Default logger
logger = setup_logger(log_file="shamin.log")
