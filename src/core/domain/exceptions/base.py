"""
File: base.py
Description: Base domain exception for HappyRobot.
Author: HappyRobot Team
Created: 2025-04-23
Last Modified: 2025-04-23

Modification History:
- 2025-04-23: Initial creation from refactoring exceptions.py.

Dependencies:
- typing
"""

from typing import Any, Dict, Optional
from uuid import UUID


class DomainException(Exception):
    """Base exception for all domain exceptions"""

    def __init__(
        self,
        message: str,
        code: str = "domain_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new domain exception

        Args:
            message: The error message
            code: The error code
            details: Additional details about the error
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary

        Returns:
            A dictionary representation of the exception
        """
        return {"message": self.message, "code": self.code, "details": self.details}


class EntityNotFoundException(DomainException):
    """Exception raised when an entity is not found"""

    def __init__(
        self, entity_type: str, entity_id: UUID, message: Optional[str] = None
    ):
        """
        Initialize a new entity not found exception

        Args:
            entity_type: The type of entity that was not found
            entity_id: The ID of the entity that was not found
            message: Optional custom error message
        """
        self.entity_type = entity_type
        self.entity_id = entity_id

        if message is None:
            message = f"{entity_type.capitalize()} with ID {entity_id} not found"

        super().__init__(
            message=message,
            code=f"{entity_type}_not_found",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class ValidationException(DomainException):
    """Exception raised when validation fails"""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ):
        """
        Initialize a new validation exception

        Args:
            message: The error message
            field: The field that failed validation
            value: The value that failed validation
        """
        details = {}

        if field is not None:
            details["field"] = field

        if value is not None:
            details["value"] = str(value)

        super().__init__(message=message, code="validation_error", details=details)


class AuthenticationException(DomainException):
    """Exception raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize a new authentication exception

        Args:
            message: The error message
        """
        super().__init__(message=message, code="authentication_error")


class AuthorizationException(DomainException):
    """Exception raised when authorization fails"""

    def __init__(
        self,
        message: str = "Authorization failed",
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
    ):
        """
        Initialize a new authorization exception

        Args:
            message: The error message
            resource_type: The type of resource that access was denied to
            resource_id: The ID of the resource that access was denied to
        """
        details = {}

        if resource_type is not None:
            details["resource_type"] = resource_type

        if resource_id is not None:
            details["resource_id"] = resource_id

        super().__init__(message=message, code="authorization_error", details=details)


class BusinessRuleViolationException(DomainException):
    """Exception raised when a business rule is violated"""

    def __init__(self, message: str, rule: Optional[str] = None):
        """
        Initialize a new business rule violation exception

        Args:
            message: The error message
            rule: The name of the business rule that was violated
        """
        details = {}

        if rule is not None:
            details["rule"] = rule

        super().__init__(
            message=message, code="business_rule_violation", details=details
        )


class ConcurrencyException(DomainException):
    """Exception raised when a concurrency conflict occurs"""

    def __init__(
        self,
        message: str = "Concurrency conflict detected",
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ):
        """
        Initialize a new concurrency exception

        Args:
            message: The error message
            entity_type: The type of entity that had a concurrency conflict
            entity_id: The ID of the entity that had a concurrency conflict
        """
        details = {}

        if entity_type is not None:
            details["entity_type"] = entity_type

        if entity_id is not None:
            details["entity_id"] = entity_id

        super().__init__(message=message, code="concurrency_error", details=details)


class InfrastructureException(DomainException):
    """Exception raised when an infrastructure error occurs"""

    def __init__(self, message: str, component: Optional[str] = None):
        """
        Initialize a new infrastructure exception

        Args:
            message: The error message
            component: The infrastructure component that failed
        """
        details = {}

        if component is not None:
            details["component"] = component

        super().__init__(message=message, code="infrastructure_error", details=details)


class BaseException(Exception):
    """Base exception for all API exceptions"""

    def __init__(self, detail: str, status_code: int = 500):
        """
        Initialize a new base exception

        Args:
            detail: The error detail message
            status_code: The HTTP status code
        """
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary

        Returns:
            A dictionary representation of the exception
        """
        return {"detail": self.detail, "status_code": self.status_code}


class NotFoundException(BaseException):
    """Exception raised when a resource is not found"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, 404)


class UnauthorizedException(BaseException):
    """Exception raised when authentication fails"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, 401)


class ForbiddenException(BaseException):
    """Exception raised when access is forbidden"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, 403)
