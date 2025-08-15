from typing import Callable
import time
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
	"""
	Rate limiting middleware to prevent API abuse.
	Implements sliding window rate limiting based on client IP.
	"""

	def __init__(self, app, requests_per_minute: int = 100):
		super().__init__(app)
		self.requests_per_minute = requests_per_minute
		self.client_requests = defaultdict(deque)
		self.window_size = 60  # 60 seconds

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		# Get client IP
		client_ip = request.client.host if request.client else "unknown"

		# Skip rate limiting for health checks
		if request.url.path in ["/health", "/api/v1/health"]:
			return await call_next(request)

		current_time = time.time()

		# Clean old requests outside the window
		requests = self.client_requests[client_ip]
		while requests and requests[0] < current_time - self.window_size:
			requests.popleft()

		# Check if rate limit exceeded
		if len(requests) >= self.requests_per_minute:
			raise HTTPException(
				status_code=429,
				detail="Rate limit exceeded. Please try again later.",
				headers={"Retry-After": "60"}
			)

		# Add current request timestamp
		requests.append(current_time)

		# Process request
		response = await call_next(request)

		# Add rate limiting headers
		response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
		response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - len(requests)))
		response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))

		return response
