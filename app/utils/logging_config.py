"""Application logging configuration built on top of loguru."""

from pathlib import Path

from loguru import logger


LOG_DIR = Path("data/dynamic/logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = (
    "{time:YYYYMMDDHHmmss} | {level:<8} | "
    "{name}:{function}:{line} | {message}"
)


def configure_logging(enabled):
    """
    Configure loguru sinks for the application.

    Returns:
        Path | None: The active log file when logging is enabled, else None.
    """
    logger.remove()

    if not enabled:
        return None

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.add(
        LOG_FILE,
        format=LOG_FORMAT,
        level="INFO",
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )
    logger.info("Logging enabled.")
    return LOG_FILE
