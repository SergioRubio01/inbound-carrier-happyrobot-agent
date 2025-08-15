"""
File: __init__.py
Description: A concise description of the file's purpose and functionality
Author: HappyRobot Team
Created: 2025-05-30
Last Modified: 2025-05-30

Modification History:
- 2025-05-30: Initial file creation

Dependencies:
- List major dependencies or related files
"""

from .base import (
    BaseException,
    BusinessRuleViolationException,
    ConcurrencyException,
    DomainException,
    EntityNotFoundException,
    InfrastructureException,
    ValidationException,
)

__all__ = [
    "NotFoundException",
    "AuthorizationException",
    "AuthenticationException",
    "SecurityViolationException",
    "DomainException",
    "EntityNotFoundException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "InfrastructureException",
    "ConcurrencyException",
    "BusinessRuleViolationException",
    "BaseException",
    "ConflictException",
    "InvalidStateTransitionException",
    "AgentExecutionException",
    "OperationNotSupportedException",
    "ResourceLimitExceededException",
    "ForbiddenException",
    "DatabaseConnectionException",
    "CacheConnectionException",
    "ConfigurationException",
    "ExternalServiceException",
    "OrganizationNotFoundException",
    "OrganizationNameAlreadyExistsException",
    "OrganizationAccessDeniedException",
    "OrganizationMemberNotFoundException",
    "OrganizationMemberAlreadyExistsException",
    "OrganizationOwnerRemovalException",
    "OrganizationSubscriptionException",
    "OrganizationLimitExceededException",
    "PermissionException",
    "RepositoryError",
    "DuplicateEntityError",
    "DataIntegrityError",
    "ValidationException",
    "ServiceException",
    "ServiceNotFoundException",
    "ServiceConnectionException",
    "ServiceAuthenticationException",
    "ServiceEndpointNotFoundException",
    "ServiceRequestException",
    "ServiceResponseParsingException",
    "ServiceRateLimitException",
    "ServiceTimeoutException",
    "ServiceStatusException",
    "UserNotFoundException",
    "UserEmailNotFoundException",
    "UserAuthenticationException",
    "UserAuthorizationException",
    "UserAlreadyExistsException",
    "InvalidPasswordException",
    "PasswordMismatchException",
    "InvalidTokenException",
    "ExpiredTokenException",
    "UseCaseError",
    "UnauthorizedException",
]
