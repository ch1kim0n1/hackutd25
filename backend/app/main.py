"""
APEX FastAPI Application
Main entry point for the APEX backend API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings, validate_settings
from app.core.logging import setup_logging
from app.api.routes import router as api_router
from app.api.websocket import websocket_router
from app.core.database import create_tables
# from app.services.seed_data import seed_test_data  # Disabled for demo
seed_test_data = None  # Placeholder

# Setup structured logging
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    logger.info("🚀 Starting APEX Backend Application")

    # Startup
    try:
        # Validate configuration
        validate_settings()
        logger.info("✅ Configuration validated")

        # Create database tables
        # await create_tables()  # Disabled for demo
        logger.info("✅ Database tables creation skipped for demo")

        # Seed test data if in development
        if settings.ENVIRONMENT == "development":
            # await seed_test_data()  # Disabled for demo
            logger.info("✅ Test data seeding skipped for demo")

        logger.info("🎉 Application startup complete")

    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down APEX Backend Application")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="APEX Multi-Agent Financial Operating System API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Security middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.CORS_ORIGINS
        )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=600,  # 10 minutes
    )

    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/ws")

    # Health check endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }

    @app.get("/ready")
    async def readiness_check():
        """Readiness check - verifies all dependencies are available"""
        # TODO: Add actual dependency checks (DB, Redis, external APIs)
        return {
            "ready": True,
            "service": settings.APP_NAME,
            "checks": {
                "database": True,  # TODO: implement actual check
                "redis": True,     # TODO: implement actual check
                "external_apis": True,  # TODO: implement actual check
            }
        }

    @app.get("/")
    async def root():
        """Root endpoint with basic service information"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "Multi-Agent Financial Operating System",
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "health": "/health",
            "ready": "/ready"
        }

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add request ID to all responses for tracing"""
        import uuid
        request_id = str(uuid.uuid4())[:8]

        # Add request ID to logger context
        logger_adapter = logging.LoggerAdapter(logger, {"request_id": request_id})
        request.state.logger = logger_adapter
        request.state.request_id = request_id

        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response

    return app


# Create the FastAPI application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
