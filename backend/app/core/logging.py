"""
Centralized logging configuration for APEX backend
Provides structured JSON logging with request IDs and proper formatting
"""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False

from app.core.settings import settings


def setup_logging():
    """Configure logging for the entire application"""

    # Create logs directory if it doesn't exist
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine formatter
    formatter_name = "text"
    if JSON_LOGGER_AVAILABLE and settings.LOG_FORMAT == "json":
        formatter_name = "json"

    # Logging configuration
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": formatter_name,
                "level": settings.LOG_LEVEL,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
        },
        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    # Add JSON formatter if available
    if JSON_LOGGER_AVAILABLE:
        log_config["formatters"]["json"] = {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

    # Add file handler if configured
    if settings.LOG_FILE:
        log_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": settings.LOG_FILE,
            "formatter": settings.LOG_FORMAT,
            "level": settings.LOG_LEVEL,
        }
        log_config["root"]["handlers"].append("file")
        for logger_name in log_config["loggers"]:
            log_config["loggers"][logger_name]["handlers"].append("file")

    # Apply configuration
    logging.config.dictConfig(log_config)

    # Set third-party loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured", extra={
        "format": settings.LOG_FORMAT,
        "level": settings.LOG_LEVEL,
        "file": settings.LOG_FILE,
        "environment": settings.ENVIRONMENT
    })


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(f"app.{name}")


class RequestLogger:
    """Utility for logging requests with consistent structure"""

    @staticmethod
    def log_request(logger: logging.Logger, operation: str, user_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """Log an API request"""
        extra = {
            "operation": operation,
            "user_id": user_id or "anonymous",
        }
        if data:
            # Sanitize sensitive data
            safe_data = RequestLogger._sanitize_data(data)
            extra["data"] = safe_data

        logger.info(f"Request: {operation}", extra=extra)

    @staticmethod
    def log_response(logger: logging.Logger, operation: str, status_code: int, duration_ms: Optional[float] = None, user_id: Optional[str] = None):
        """Log an API response"""
        extra = {
            "operation": operation,
            "status_code": status_code,
            "user_id": user_id or "anonymous",
        }
        if duration_ms is not None:
            extra["duration_ms"] = duration_ms

        if status_code >= 400:
            logger.warning(f"Response: {operation} - {status_code}", extra=extra)
        else:
            logger.info(f"Response: {operation} - {status_code}", extra=extra)

    @staticmethod
    def _sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive data from logs"""
        sensitive_keys = {"password", "token", "secret", "key", "api_key"}
        sanitized = {}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = RequestLogger._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized


# Global logger instance
logger = get_logger(__name__)
