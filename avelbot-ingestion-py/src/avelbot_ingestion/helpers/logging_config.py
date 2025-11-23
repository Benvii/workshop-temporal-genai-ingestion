import logging
import os
import sys

logging_level = logging.getLevelName(os.getenv("LOGGING_LEVEL", "INFO"))
temporal_logging_level = logging.getLevelName(os.getenv("TEMPORAL_LOGGING_LEVEL", "INFO"))

APP_LOGGER_NAME = "ingestion-workflow"


def get_app_logger(name: str = None):
    return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")


class DevPrettyFormatter(logging.Formatter):
    """
    Colorful, human-readable formatter that shows all log fields in dev mode.
    """

    COLORS = {
        "DEBUG": "\033[94m",  # blue
        "INFO": "\033[92m",  # green
        "WARNING": "\033[93m",  # yellow
        "ERROR": "\033[91m",  # red
        "CRITICAL": "\033[95m",  # magenta
        "ENDC": "\033[0m",
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["ENDC"]

        # Base log line
        log = f"{level_color}[{record.levelname}] {record.name}:{record.lineno}{reset} - {record.getMessage()}"

        # Extract extra fields (filter out std ones)
        std_keys = set(vars(logging.LogRecord("", "", "", "", "", (), None)))
        extras = {k: v for k, v in record.__dict__.items() if k not in std_keys and not k.startswith("_")}

        # Append extras in a readable way
        if extras:
            log += " | " + " ".join(f"{k}={v}" for k, v in extras.items())

        return log


class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # Inject bound context into every log record
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


def configure_logging(caller: str):
    """Call this once at app startup to configure logging globally."""
    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(DevPrettyFormatter())

    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(logging_level)
    app_logger.handlers.clear()
    app_logger.addHandler(handler)
    app_logger.propagate = False

    temporalio_logger = logging.getLogger("temporalio")
    temporalio_logger.setLevel(temporal_logging_level)
    temporalio_logger.addHandler(handler)
    temporalio_logger.propagate = False

    logging.debug(
        f"Logging initialized for {caller}. - Level: {logging.getLevelName(logging_level)} - Temporal level: {logging.getLevelName(temporal_logging_level)}"
    )
