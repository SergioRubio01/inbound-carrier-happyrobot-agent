import os
from typing import Callable, Iterable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

EXEMPT_PATH_PREFIXES: Iterable[str] = (
    "/health",
    "/api/v1/health",
    "/api/v1/openapi.json",
    "/api/v1/docs",
    "/api/v1/redoc",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Simple API Key authentication middleware.
    Looks for X-API-Key header or Authorization: ApiKey <key>.
    """

    def __init__(self, app):
        super().__init__(app)
        self.expected_key = os.getenv("API_KEY", "dev-local-api-key")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        provided_key = request.headers.get(
            "X-API-Key"
        ) or self._extract_from_authorization(request.headers.get("Authorization"))

        if not provided_key or provided_key != self.expected_key:
            return Response(status_code=401, content=b"Unauthorized")

        return await call_next(request)

    @staticmethod
    def _extract_from_authorization(value: str | None) -> str | None:
        if not value:
            return None
        prefix = "ApiKey "
        if value.startswith(prefix):
            return value[len(prefix) :].strip()
        return None
