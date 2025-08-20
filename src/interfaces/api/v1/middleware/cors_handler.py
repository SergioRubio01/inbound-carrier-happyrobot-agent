"""
CORS Handler Middleware

Ensures proper handling of CORS preflight requests, especially for admin endpoints.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class CORSHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure CORS preflight requests are handled properly.

    This middleware runs before other middleware to ensure OPTIONS requests
    get proper CORS headers even if authentication fails.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle the request, with special handling for OPTIONS requests.
        """
        # For OPTIONS requests, return early with CORS headers
        if request.method == "OPTIONS":
            response = StarletteResponse(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "3600"
            response.headers["Access-Control-Expose-Headers"] = "*"

            logger.debug(f"Handled OPTIONS request for {request.url.path}")
            return response  # type: ignore[return-value]

        # For other requests, proceed normally
        response = await call_next(request)

        # Ensure CORS headers are present on all responses
        if "access-control-allow-origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "*"

        return response  # type: ignore[return-value]
