"""
File: security_headers.py
Description: Security headers middleware for adding HTTP security headers to responses.
Author: HappyRobot Team
Created: 2025-08-20
Last Modified: 2025-08-20

Modification History:
- 2025-08-20: Initial creation with comprehensive security headers.

Dependencies:
- fastapi
- starlette
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to HTTP responses.

    This middleware adds various security headers to improve the security posture
    of the application, including headers for HTTPS enforcement, content security policy,
    clickjacking protection, and more.
    """

    def __init__(self, app, enable_hsts: bool = False):
        """
        Initialize the security headers middleware.

        Args:
            app: The FastAPI application instance
            enable_hsts: Whether to enable HTTP Strict Transport Security (HSTS).
                        Should only be enabled when serving over HTTPS.
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to the response.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response with security headers added
        """
        try:
            # Process the request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response, request)

            return response

        except Exception as e:
            logger.error(f"Error in SecurityHeadersMiddleware: {e}")
            # If there's an error, still try to add basic security headers
            response = await call_next(request)
            self._add_basic_security_headers(response)
            return response

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """
        Add comprehensive security headers to the response.

        Args:
            response: The HTTP response to modify
            request: The incoming HTTP request (for context)
        """
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Enable XSS filtering (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content-Security-Policy: Prevent XSS and data injection attacks
        # This is a restrictive policy suitable for an API
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Permissions-Policy: Control browser features
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # Cross-Origin-Opener-Policy: Isolate browsing context
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cross-Origin-Embedder-Policy: Control cross-origin resource embedding
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cross-Origin-Resource-Policy: Control cross-origin resource access
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cache-Control: Prevent caching of sensitive data
        # For API responses, generally avoid caching unless specifically needed
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        else:
            # For non-sensitive endpoints like health checks, allow brief caching
            response.headers["Cache-Control"] = "public, max-age=60"

        # HTTP Strict Transport Security (HSTS) - only if HTTPS is enabled
        if self.enable_hsts:
            # Include subdomains and preload for maximum security
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Server header: Remove or minimize server information disclosure
        response.headers["Server"] = "HappyRobot-API"

        # Custom security header for application identification
        response.headers["X-Powered-By"] = "HappyRobot-FDE"

    def _add_basic_security_headers(self, response: Response) -> None:
        """
        Add basic security headers in case of error.

        Args:
            response: The HTTP response to modify
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """
        Determine if an endpoint contains sensitive data that should not be cached.

        Args:
            path: The request path

        Returns:
            True if the endpoint is sensitive and should not be cached
        """
        # Health check endpoints can be cached briefly
        if path in ["/health", "/api/v1/health"]:
            return False

        # Documentation endpoints can be cached
        if any(doc_path in path for doc_path in ["/docs", "/redoc", "/openapi.json"]):
            return False

        # All other API endpoints contain sensitive business data
        if path.startswith("/api/"):
            return True

        # Default to sensitive for unknown endpoints
        return True
