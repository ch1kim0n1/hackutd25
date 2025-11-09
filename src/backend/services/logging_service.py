"""
Structured logging service for APEX with correlation IDs and request tracking.
"""
import logging
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import traceback
import sys

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(LOG_DIR, exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Includes correlation IDs, timestamps, and stack traces for errors.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
            "user_id": getattr(record, "user_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
            "status_code": getattr(record, "status_code", None),
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            # Sanitize sensitive info from traceback
            log_data["exception"]["traceback"] = [
                line for line in log_data["exception"]["traceback"]
                if not any(secret in line for secret in ["password", "token", "key", "secret"])
            ]

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Write logs to file
        log_to_console: Write logs to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("apex")
    logger.setLevel(getattr(logging, log_level))

    formatter = StructuredFormatter()

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        log_file = os.path.join(LOG_DIR, "apex.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Error log file (errors and above)
        error_log = os.path.join(LOG_DIR, "apex_errors.log")
        error_handler = logging.FileHandler(error_log)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    return logger


class RequestLogger:
    """Utility for logging HTTP requests/responses with correlation IDs"""

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate unique correlation ID for request tracking"""
        return f"req_{uuid4().hex[:12]}"

    @staticmethod
    def log_request(
        logger: logging.Logger,
        method: str,
        path: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        query_params: Optional[Dict] = None
    ):
        """Log incoming HTTP request"""
        extra = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "path": path,
            "method": method,
        }
        logger.info(
            f"{method} {path}",
            extra=extra
        )

    @staticmethod
    def log_response(
        logger: logging.Logger,
        method: str,
        path: str,
        status_code: int,
        correlation_id: str,
        user_id: Optional[str] = None,
        duration_ms: float = 0
    ):
        """Log HTTP response"""
        extra = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "path": path,
            "method": method,
            "status_code": status_code,
        }

        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        logger.log(
            level,
            f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)",
            extra=extra
        )

    @staticmethod
    def log_error(
        logger: logging.Logger,
        error: Exception,
        correlation_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log error with full context"""
        extra = {
            "correlation_id": correlation_id,
            "user_id": user_id,
        }
        if context:
            extra.update(context)

        logger.error(
            f"Error: {error.__class__.__name__}: {str(error)}",
            exc_info=True,
            extra=extra
        )


class ErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def format_error(
        error_code: str,
        message: str,
        correlation_id: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format error response.

        Args:
            error_code: Application-specific error code (e.g., "AUTH_FAILED")
            message: Human-readable error message
            correlation_id: Request correlation ID for tracing
            status_code: HTTP status code
            details: Additional error details (non-sensitive)

        Returns:
            Formatted error response dict
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": status_code,
            }
        }

        if details:
            response["error"]["details"] = details

        return response

    @staticmethod
    def sanitize_message(message: str) -> str:
        """
        Sanitize error message by removing sensitive information.

        Args:
            message: Raw error message

        Returns:
            Sanitized message
        """
        sensitive_patterns = [
            "password",
            "token",
            "api_key",
            "secret",
            "credential",
            "auth",
            "file://",
            "/home/",
            "/root/",
            "C:\\",
            "SELECT ",
            "INSERT ",
            "UPDATE ",
            "DELETE ",
        ]

        sanitized = message
        for pattern in sensitive_patterns:
            if pattern.lower() in message.lower():
                sanitized = f"An error occurred. Please contact support with correlation ID."
                break

        return sanitized


# Initialize global logger
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_to_file=True,
    log_to_console=True
)
