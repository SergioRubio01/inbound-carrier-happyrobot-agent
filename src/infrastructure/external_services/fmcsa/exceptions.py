"""
File: exceptions.py
Description: FMCSA API specific exceptions
Author: HappyRobot Team
Created: 2024-11-15
"""

from typing import Optional


class FMCSAServiceError(Exception):
    """Base exception for FMCSA service errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.retry_after = retry_after


class FMCSAAPIError(FMCSAServiceError):
    """Raised when FMCSA API returns an error response."""
    pass


class FMCSATimeoutError(FMCSAServiceError):
    """Raised when FMCSA API request times out."""
    pass


class FMCSAAuthenticationError(FMCSAServiceError):
    """Raised when FMCSA API authentication fails."""
    pass


class FMCSARateLimitError(FMCSAServiceError):
    """Raised when FMCSA API rate limit is exceeded."""
    pass


class FMCSAValidationError(FMCSAServiceError):
    """Raised when FMCSA API returns invalid data."""
    pass


class FMCSACarrierNotFoundError(FMCSAServiceError):
    """Raised when carrier is not found in FMCSA system."""
    pass


class FMCSAServiceUnavailableError(FMCSAServiceError):
    """Raised when FMCSA service is temporarily unavailable."""
    pass
