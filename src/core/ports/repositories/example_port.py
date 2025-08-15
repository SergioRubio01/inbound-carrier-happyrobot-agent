# from abc import ABC, abstractmethod
# from typing import List, Optional
# from uuid import UUID

# from HappyRobot.core.domain.entities.organization import Organization
# from HappyRobot.core.domain.entities.user import User
# from HappyRobot.core.domain.value_objects.email import Email


# class UserPort(ABC):
#     """Interface for user repository"""

#     @abstractmethod
#     async def create(self, user: User) -> User:
#         """Create a new user"""
#         pass

#     @abstractmethod
#     async def update(self, user: User) -> User:
#         """Update an existing user (including potentially active organization_id)"""
#         pass

#     @abstractmethod
#     async def get_by_id(self, user_id: UUID) -> Optional[User]:
#         """Get a user by ID"""
#         pass

#     @abstractmethod
#     async def get_by_email(self, email: Email) -> Optional[User]:
#         """Get a user by email"""
#         pass

#     @abstractmethod
#     async def delete(self, user_id: UUID) -> bool:
#         """Delete a user"""
#         pass

#     @abstractmethod
#     async def list_by_organization(self, organization_id: UUID) -> List[User]:
#         """List users who are members of a specific organization (via association table).
#         Note: Does not typically include the user's role *within* this specific organization.
#         Use get_user_role_in_organization for specific role information.
#         """
#         pass

#     @abstractmethod
#     async def generate_id(self) -> UUID:
#         """Generate a unique ID for a user"""
#         pass

#     @abstractmethod
#     async def add_user_to_organization(
#         self, user_id: UUID, organization_id: UUID, role: str
#     ):
#         """Adds a user membership record to an organization with a specific role."""
#         pass

#     @abstractmethod
#     async def remove_user_from_organization(
#         self, user_id: UUID, organization_id: UUID
#     ) -> bool:
#         """Removes a user membership record from an organization."""
#         pass

#     @abstractmethod
#     async def list_user_organizations(self, user_id: UUID) -> List[Organization]:
#         """Lists all organizations a user is a member of."""
#         pass

#     @abstractmethod
#     async def update_user_role_in_organization(
#         self, user_id: UUID, organization_id: UUID, new_role: str
#     ) -> bool:
#         """Updates a user's role within a specific organization membership."""
#         pass

#     @abstractmethod
#     async def is_user_member_of(self, user_id: UUID, organization_id: UUID) -> bool:
#         """Checks if a user is a member of a specific organization."""
#         pass

#     @abstractmethod
#     async def get_organization_member_count(self, organization_id: UUID) -> int:
#         """Gets the number of members in an organization."""
#         pass

#     @abstractmethod
#     async def get_user_organization_count(self, user_id: UUID) -> int:
#         """Gets the number of organizations a user is a member of."""
#         pass

#     @abstractmethod
#     async def get_user_role_in_organization(
#         self, user_id: UUID, organization_id: UUID
#     ) -> Optional[str]:
#         """Gets a user's role within a specific organization."""
#         pass
