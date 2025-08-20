from .base import DomainException


class DatabaseConnectionException(DomainException):
    """Exception raised for database connection errors"""

    # Renamed from DatabaseConnectionError for consistency
    pass


class CacheConnectionException(DomainException):
    """Exception raised for cache connection errors"""

    # Renamed from CacheConnectionError for consistency
    pass


class ConfigurationException(DomainException):
    """Exception raised for configuration errors"""

    # Renamed from ConfigurationError for consistency
    pass


class ExternalServiceException(DomainException):
    """Exception raised for external service errors"""

    # Renamed from ExternalServiceError for consistency
    pass
