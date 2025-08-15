from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
	"""
	No-op placeholder for rate limiting. Can be replaced with a proper implementation.
	"""

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		return await call_next(request)
