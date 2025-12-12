"""
Logging Configuration for Game Service.

Controls security event logging behavior.
Set ENABLE_SECURITY_LOGGING to False to disable detailed security logs.
"""

import os
import logging

# ============================================================
# SECURITY LOGGING CONFIGURATION
# ============================================================

# Enable/disable security event logging
ENABLE_SECURITY_LOGGING = os.getenv("ENABLE_SECURITY_LOGGING", "true").lower() == "true"

# Log level for security events
SECURITY_LOG_LEVEL = os.getenv("SECURITY_LOG_LEVEL", "INFO").upper()

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================
# LOGGER SETUP
# ============================================================

def setup_security_logger(name: str) -> logging.Logger:
    """
    Setup a logger with security logging configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, SECURITY_LOG_LEVEL, logging.INFO))

    return logger


# ============================================================
# SECURITY LOGGING HELPERS
# ============================================================

def log_if_enabled(logger: logging.Logger, level: str, message: str):
    """
    Log message only if security logging is enabled.

    Args:
        logger: Logger instance
        level: Log level (INFO, WARNING, ERROR)
        message: Log message
    """
    if not ENABLE_SECURITY_LOGGING:
        return

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)

