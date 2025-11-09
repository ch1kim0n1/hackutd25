"""
Global exception handlers and error middleware for FastAPI.
Converts all exceptions to structured JSON responses with correlation IDs.
"""
from typing import Callable, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import time
import logging
from services.logging_service import (
    RequestLogger,
    ErrorResponse,
    logger
)

# Create logger
app_logger = logger


class ExceptionMiddleware:
    """Middleware to handle exceptions globally with correlation IDs"""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable):
        """
        Process request with exception handling and request logging.
        """
        correlation_id = RequestLogger.generate_correlation_id()
        request.state.correlation_id = correlation_id

        # Extract user ID if authenticated
        user_id = None
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id = str(request.state.user.id)

        # Log incoming request
        RequestLogger.log_request(
            app_logger,
            request.method,
            request.url.path,
            correlation_id,
            user_id
        )

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000

            # Log response
            RequestLogger.log_response(
                app_logger,
                request.method,
                request.url.path,
                response.status_code,
                correlation_id,
                user_id,
                duration
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            duration = (time.time() - start_time) * 1000

            # Log error
            RequestLogger.log_error(
                app_logger,
                exc,
                correlation_id,
                user_id,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration,
                }
            )

            # Return error response
            error_response = ErrorResponse.format_error(
                error_code="INTERNAL_SERVER_ERROR",
                message="An internal server error occurred",
                correlation_id=correlation_id,
                status_code=500
            )

            response = JSONResponse(
                status_code=500,
                content=error_response
            )
            response.headers["X-Correlation-ID"] = correlation_id

            return response


def setup_exception_handlers(app: FastAPI):
    """
    Configure all exception handlers for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """

    # Add middleware
    app.add_middleware(ExceptionMiddleware)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exception"""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        RequestLogger.log_error(
            app_logger,
            exc,
            correlation_id,
            context={
                "path": request.url.path,
                "method": request.method,
            }
        )

        error_response = ErrorResponse.format_error(
            error_code="INTERNAL_ERROR",
            message=ErrorResponse.sanitize_message(str(exc)),
            correlation_id=correlation_id,
            status_code=500
        )

        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Correlation-ID": correlation_id}
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors"""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        error_response = ErrorResponse.format_error(
            error_code="VALIDATION_ERROR",
            message=ErrorResponse.sanitize_message(str(exc)),
            correlation_id=correlation_id,
            status_code=400
        )

        return JSONResponse(
            status_code=400,
            content=error_response,
            headers={"X-Correlation-ID": correlation_id}
        )

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """Handle missing key errors"""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        error_response = ErrorResponse.format_error(
            error_code="NOT_FOUND",
            message="Requested resource not found",
            correlation_id=correlation_id,
            status_code=404
        )

        return JSONResponse(
            status_code=404,
            content=error_response,
            headers={"X-Correlation-ID": correlation_id}
        )

    @app.exception_handler(TimeoutError)
    async def timeout_handler(request: Request, exc: TimeoutError):
        """Handle timeout errors"""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        error_response = ErrorResponse.format_error(
            error_code="TIMEOUT",
            message="Request timed out",
            correlation_id=correlation_id,
            status_code=504
        )

        return JSONResponse(
            status_code=504,
            content=error_response,
            headers={"X-Correlation-ID": correlation_id}
        )
