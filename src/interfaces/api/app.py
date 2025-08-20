import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.domain.exceptions import (
    BaseException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from src.config.settings import settings

# Import custom middleware
from src.interfaces.api.v1.middleware import (
    AuthenticationMiddleware,
    CORSHandlerMiddleware,
    RateLimiterMiddleware,
)

logger_app = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        # Define OpenAPI tags with descriptions and ordering
        openapi_tags=[
            {
                "name": "Calls",
                "description": "Operations for calls",
            },
            {
                "name": "Metrics",
                "description": "Operations for metrics",
            },
            {
                "name": "Negotiations",
                "description": "Operations for negotiations",
            },
            {
                "name": "FMCSA",
                "description": "Operations for FMCSA",
            },
            {
                "name": "Loads",
                "description": "Operations for loads",
            },
        ],
    )

    # Add health check endpoints BEFORE middleware to ensure fast response
    # These endpoints bypass all middleware processing
    # @app.get("/health")
    # async def root_health_check():
    #     """Root health check endpoint for load balancer"""
    #     return {"status": "ok", "service": "HappyRobot FDE API", "version": "0.1.0"}

    @app.get("/api/v1/health")
    async def api_health_check():
        """API health check endpoint for load balancer"""
        return {"status": "ok"}

    # Add middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )

    # Add custom middleware (order is important - last added runs first)
    # Rate limiter to prevent abuse (runs third)
    app.add_middleware(RateLimiterMiddleware)
    # AuthMiddleware for user authentication and role checks (runs second)
    app.add_middleware(AuthenticationMiddleware)
    # CORSHandlerMiddleware first to handle OPTIONS requests (runs first)
    app.add_middleware(CORSHandlerMiddleware)

    # Add exception handlers
    @app.exception_handler(BaseException)
    async def base_exception_handler(request: Request, exc: BaseException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_exception_handler(
        request: Request, exc: UnauthorizedException
    ):
        return JSONResponse(status_code=401, content={"detail": exc.detail})

    @app.exception_handler(ForbiddenException)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
        return JSONResponse(status_code=403, content={"detail": exc.detail})

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(status_code=422, content={"detail": exc.details})

    # Include API routers
    from src.interfaces.api.v1 import fmcsa, loads, negotiations, calls, metrics

    app.include_router(fmcsa.router, prefix="/api/v1")
    app.include_router(loads.router, prefix="/api/v1")
    app.include_router(negotiations.router, prefix="/api/v1")
    app.include_router(calls.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")

    # Add startup event handler
    @app.on_event("startup")
    async def startup_event():
        logger_app.info("Application startup...")

    return app
