"""
File: __init__.py
Description: Initializes the middleware module, making middleware classes available.
Author: HappyRobot Team
Created: 2025-05-25
Last Modified: 2025-05-25

Modification History:
- 2025-05-25: Initial creation and export of middleware classes.

Dependencies:
- .auth_middleware
- .rate_limiter
- .cors_handler
"""

from .auth_middleware import AuthenticationMiddleware
from .rate_limiter import RateLimiterMiddleware
from .cors_handler import CORSHandlerMiddleware

__all__ = ["AuthenticationMiddleware", "RateLimiterMiddleware", "CORSHandlerMiddleware"]
