# import logging
# import uuid
# from datetime import datetime
# from typing import List, Optional
# from uuid import UUID

# from sqlalchemy import delete, select, update
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.ext.asyncio import AsyncSession

# from HappyRobot.core.domain.entities.organization import (
#     Organization,
#     OrganizationBusinessField,
#     OrganizationStatus,
#     OrganizationSubscription,
#     OrganizationType,
# )
# from HappyRobot.core.domain.entities.user import User, UserRole, UserStatus
# from HappyRobot.core.domain.value_objects.email import Email
# from HappyRobot.core.ports.repositories.user_repository import UserPort
# from HappyRobot.infrastructure.database.models.organization_model import (
#     OrganizationModel,
# )
# from HappyRobot.infrastructure.database.models.user_model import UserModel

# logger = logging.getLogger(__name__)


# class PostgresUserRepository(UserPort):
#     """PostgreSQL ORM implementation for UserPort."""

#     def __init__(self, session: AsyncSession):
#         self.session = session

#     # --- Helper: Entity/Model Mapping ---

#     def _map_role(self, role_value: str) -> UserRole:
#         """Map role value to UserRole enum with fallback to MEMBER for invalid values."""
#         try:
#             # Try exact match first
#             return UserRole(role_value)
#         except ValueError:
#             # Handle legacy 'user' role or any other invalid values
#             if role_value.lower() == 'user':
#                 logger.warning(f"Mapping legacy role 'user' to 'member' for better compatibility")
#                 return UserRole.MEMBER
#             else:
#                 logger.error(f"Invalid role value '{role_value}', defaulting to MEMBER")
#                 return UserRole.MEMBER

#     def _map_model_to_entity(self, model: UserModel) -> User:
#         user_data = {
#             "id": model.id,
#             "email": Email(value=model.email),
#             "name": model.name,
#             "last_name": model.last_name,
#             "hashed_password": model.hashed_password,
#             "is_verified": model.is_verified,
#             "status": UserStatus(model.status),
#             "role": self._map_role(model.role),  # Map the role field with validation
#             "organization_id": (
#                 str(model.organization_id) if model.organization_id else None
#             ),
#             "last_login": model.last_login_at,
#             "metadata": model.preferences or {},
#             "preferences": model.preferences or {},
#             "created_at": model.created_at,
#             "updated_at": model.updated_at,
#             "oauth_accounts": [],
#             "avatar": model.profile_picture,
#             "avatar_color": model.avatar_color,
#         }
#         return User(**user_data)

#     def _to_entity(self, model: UserModel) -> User:
#         # Alias
#         return self._map_model_to_entity(model)

#     def _map_org_model_to_entity(self, model: OrganizationModel) -> Organization:
#         try:
#             org_type = OrganizationType(model.organization_type)
#         except ValueError:
#             org_type = OrganizationType.ENTERPRISE
#         try:
#             subscription = OrganizationSubscription(model.subscription_tier)
#         except ValueError:
#             subscription = OrganizationSubscription.FREE
#         try:
#             status = OrganizationStatus(model.status)
#         except ValueError:
#             status = OrganizationStatus.INACTIVE

#         business_field = None
#         if model.business_field:
#             try:
#                 business_field = OrganizationBusinessField(model.business_field)
#             except ValueError:
#                 business_field = OrganizationBusinessField.OTHER

#         return Organization(
#             id=model.id,
#             owner_id=model.owner_id,
#             name=model.name,
#             description=model.description,
#             status=status,
#             organization_type=org_type,
#             subscription=subscription,
#             business_field=business_field,
#             size=model.size,
#             settings=model.settings or {},
#             created_at=model.created_at,
#             updated_at=model.updated_at,
#             payment_method=None,
#             payment_status=None,
#         )

#     # --- Core User Methods ---

#     async def generate_id(self) -> UUID:
#         """Generate a unique ID for a user."""
#         return uuid.uuid4()

#     async def create(self, user: User) -> User:
#         """Creates a new user in the database."""
#         try:
#             # Convert UUID if needed
#             user_id = user.id
#             if isinstance(user_id, str):
#                 user_id = uuid.UUID(user_id)
#             elif not isinstance(user_id, uuid.UUID):
#                 raise ValueError(f"Invalid UUID format for user ID: {user_id}")

#             # Convert organization_id if present
#             org_id = user.organization_id
#             if org_id:
#                 if isinstance(org_id, str):
#                     org_id = uuid.UUID(org_id)
#                 elif not isinstance(org_id, uuid.UUID):
#                     raise ValueError(
#                         f"Invalid UUID format for organization ID: {org_id}"
#                     )

#             # Create user model
#             user_model = UserModel(
#                 id=user_id,
#                 email=str(user.email),
#                 name=user.name,
#                 last_name=user.last_name,
#                 hashed_password=user.hashed_password,
#                 status=user.status.value,
#                 role=user.role.value,  # Include the role field
#                 is_verified=user.is_verified,
#                 organization_id=org_id,
#                 created_at=user.created_at,
#                 updated_at=user.updated_at,
#                 preferences=user.preferences,
#                 last_login_at=user.last_login,
#                 profile_picture=user.avatar,
#                 avatar_color=user.avatar_color,
#             )

#             self.session.add(user_model)
#             await self.session.flush()

#             # Query the user again to get fresh data
#             updated_user = await self.session.execute(
#                 select(UserModel).where(UserModel.id == user_model.id)
#             )
#             user_model = updated_user.scalar_one()

#             return self._map_model_to_entity(user_model)

#         except Exception as e:
#             logger.error(f"Unexpected error creating user {user.email}: {str(e)}")
#             raise

#     async def update(self, user: User) -> User:
#         """Updates a user in the database."""
#         try:
#             # Get existing user
#             stmt = select(UserModel).where(UserModel.id == user.id)
#             result = await self.session.execute(stmt)
#             user_model = result.scalar_one_or_none()

#             if not user_model:
#                 raise ValueError(f"User with ID {user.id} not found for update.")

#             # Convert organization_id if present
#             org_id = user.organization_id
#             if org_id:
#                 if isinstance(org_id, str):
#                     org_id = uuid.UUID(org_id)
#                 elif not isinstance(org_id, uuid.UUID):
#                     raise ValueError(
#                         f"Invalid UUID format for organization ID: {org_id}"
#                     )

#             # Update fields
#             user_model.email = str(user.email)
#             user_model.name = user.name
#             user_model.last_name = user.last_name
#             user_model.hashed_password = user.hashed_password
#             user_model.status = user.status.value
#             user_model.role = user.role.value  # Update the role field
#             user_model.is_verified = user.is_verified
#             user_model.organization_id = org_id
#             user_model.last_login_at = user.last_login
#             user_model.preferences = user.preferences
#             user_model.profile_picture = user.avatar
#             user_model.avatar_color = user.avatar_color
#             user_model.updated_at = datetime.utcnow()

#             await self.session.flush()

#             # Query the user again to get fresh data
#             updated_user = await self.session.execute(
#                 select(UserModel).where(UserModel.id == user_model.id)
#             )
#             user_model = updated_user.scalar_one()

#             return self._map_model_to_entity(user_model)
#         except SQLAlchemyError as e:
#             logger.error(f"Database error updating user {user.id}: {e}", exc_info=True)
#             raise
#         except Exception as e:
#             logger.error(
#                 f"Unexpected error updating user {user.id}: {e}", exc_info=True
#             )
#             raise

#     async def get_by_id(self, user_id: UUID) -> Optional[User]:
#         """Get a user by ID."""
#         try:
#             stmt = select(UserModel).where(UserModel.id == user_id)
#             result = await self.session.execute(stmt)
#             model = result.scalar_one_or_none()
#             return self._map_model_to_entity(model) if model else None
#         except ValueError:
#             logger.warning(f"Invalid UUID format for user ID: {user_id}")
#             return None
#         except Exception as e:
#             logger.error(f"Error getting user by ID {user_id}: {e}", exc_info=True)
#             return None

#     async def get_by_email(self, email: Email) -> Optional[User]:
#         """Get a user by email."""
#         try:
#             stmt = select(UserModel).where(UserModel.email == str(email))
#             result = await self.session.execute(stmt)
#             model = result.scalar_one_or_none()
#             return self._map_model_to_entity(model) if model else None
#         except Exception as e:
#             logger.error(
#                 f"Error getting user by email {str(email)}: {e}", exc_info=True
#             )
#             return None

#     async def delete(self, user_id: UUID) -> bool:
#         """Delete a user."""
#         try:
#             stmt = delete(UserModel).where(UserModel.id == user_id)
#             result = await self.session.execute(stmt)
#             await self.session.commit()
#             deleted_count = result.rowcount
#             if deleted_count > 0:
#                 logger.info(f"Deleted user {user_id}")
#             else:
#                 logger.warning(
#                     f"Attempted to delete user {user_id}, but no rows affected."
#                 )
#             return deleted_count > 0
#         except ValueError:
#             logger.error(f"Invalid UUID format for user ID: {user_id}")
#             return False
#         except SQLAlchemyError as e:
#             logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
#             return False
#         except Exception as e:
#             logger.error(
#                 f"Unexpected error deleting user {user_id}: {e}", exc_info=True
#             )
#             return False

#     async def list_by_organization(self, organization_id: UUID) -> List[User]:
#         """List users who belong to a specific organization."""
#         try:
#             stmt = select(UserModel).where(UserModel.organization_id == organization_id)
#             result = await self.session.execute(stmt)
#             user_models = result.scalars().all()
#             return [self._map_model_to_entity(model) for model in user_models]
#         except ValueError:
#             logger.warning(
#                 f"Invalid UUID format for organization ID: {organization_id}"
#             )
#             return []
#         except Exception as e:
#             logger.error(
#                 f"Error listing users for org {organization_id}: {e}",
#                 exc_info=True,
#             )
#             return []

#     async def is_user_member_of(self, user_id: UUID, organization_id: UUID) -> bool:
#         """Checks if a user belongs to a specific organization."""
#         try:
#             stmt = select(UserModel).where(
#                 (UserModel.id == user_id)
#                 & (UserModel.organization_id == organization_id)
#             )
#             result = await self.session.execute(stmt)
#             user = result.scalar_one_or_none()
#             return user is not None
#         except Exception as e:
#             logger.error(
#                 f"Error checking membership for user {user_id} in org {organization_id}: {e}",
#                 exc_info=True,
#             )
#             return False

#     async def get_organization_member_count(self, organization_id: UUID) -> int:
#         """Gets the number of users in an organization."""
#         try:
#             stmt = select(UserModel).where(UserModel.organization_id == organization_id)
#             result = await self.session.execute(stmt)
#             users = result.scalars().all()
#             return len(users)
#         except Exception as e:
#             logger.error(
#                 f"Error counting users for org {organization_id}: {e}",
#                 exc_info=True,
#             )
#             return 0

#     async def add_user_to_organization(
#         self, user_id: UUID, organization_id: UUID, role: str
#     ):
#         """Updates a user's organization."""
#         try:
#             stmt = (
#                 update(UserModel)
#                 .where(UserModel.id == user_id)
#                 .values(organization_id=organization_id)
#             )
#             await self.session.execute(stmt)
#             await self.session.commit()
#             logger.info(f"Updated user {user_id} organization to {organization_id}")
#         except Exception as e:
#             logger.error(
#                 f"Error updating organization for user {user_id}: {e}",
#                 exc_info=True,
#             )
#             raise

#     async def remove_user_from_organization(
#         self, user_id: UUID, organization_id: UUID
#     ) -> bool:
#         """Removes a user from their organization if it matches the given organization_id."""
#         try:
#             stmt = (
#                 update(UserModel)
#                 .where(
#                     (UserModel.id == user_id)
#                     & (UserModel.organization_id == organization_id)
#                 )
#                 .values(organization_id=None)
#             )
#             result = await self.session.execute(stmt)
#             await self.session.commit()
#             rows_affected = result.rowcount
#             if rows_affected > 0:
#                 logger.info(
#                     f"Removed user {user_id} from organization {organization_id}"
#                 )
#             return rows_affected > 0
#         except Exception as e:
#             logger.error(
#                 f"Error removing user {user_id} from organization: {e}",
#                 exc_info=True,
#             )
#             return False

#     async def list_user_organizations(self, user_id: UUID) -> List[Organization]:
#         """Lists the user's organization (returns a list with 0 or 1 items)."""
#         try:
#             stmt = (
#                 select(OrganizationModel)
#                 .join(UserModel, UserModel.organization_id == OrganizationModel.id)
#                 .where(UserModel.id == user_id)
#             )
#             result = await self.session.execute(stmt)
#             org_model = result.scalar_one_or_none()
#             return [self._map_org_model_to_entity(org_model)] if org_model else []
#         except Exception as e:
#             logger.error(
#                 f"Error getting organization for user {user_id}: {e}",
#                 exc_info=True,
#             )
#             return []

#     async def update_user_role_in_organization(
#         self, user_id: UUID, organization_id: UUID, new_role: str
#     ) -> bool:
#         """
#         This method is maintained for interface compatibility but does nothing in the
#         single-organization model where roles are handled separately.
#         """
#         logger.info(
#             "update_user_role_in_organization called but ignored - roles are handled separately"
#         )
#         return True

#     async def get_user_role_in_organization(
#         self, user_id: UUID, organization_id: UUID
#     ) -> Optional[str]:
#         """
#         This method is maintained for interface compatibility but always returns 'member'
#         in the single-organization model where roles are handled separately.
#         """
#         try:
#             is_member = await self.is_user_member_of(user_id, organization_id)
#             return "member" if is_member else None
#         except Exception as e:
#             logger.error(
#                 f"Error checking role for user {user_id} in org {organization_id}: {e}",
#                 exc_info=True,
#             )
#             return None

#     async def get_user_organization_count(self, user_id: UUID) -> int:
#         """Gets the number of organizations a user belongs to (0 or 1)."""
#         try:
#             stmt = select(UserModel).where(
#                 (UserModel.id == user_id) & (UserModel.organization_id.isnot(None))
#             )
#             result = await self.session.execute(stmt)
#             user = result.scalar_one_or_none()
#             return 1 if user and user.organization_id else 0
#         except Exception as e:
#             logger.error(
#                 f"Error counting organizations for user {user_id}: {e}",
#                 exc_info=True,
#             )
#             return 0

#     # --- Admin Methods ---

#     async def count_users(
#         self,
#         status_filter: Optional[str] = None,
#         role_filter: Optional[str] = None,
#         organization_id_filter: Optional[UUID] = None,
#         search_query: Optional[str] = None,
#     ) -> int:
#         """Count users with optional filters."""
#         try:
#             stmt = select(UserModel)

#             # Apply filters
#             if status_filter:
#                 stmt = stmt.where(UserModel.status == status_filter)

#             if role_filter:
#                 stmt = stmt.where(UserModel.role == role_filter)

#             if organization_id_filter:
#                 stmt = stmt.where(UserModel.organization_id == organization_id_filter)

#             if search_query:
#                 search_term = f"%{search_query}%"
#                 stmt = stmt.where(
#                     (UserModel.email.ilike(search_term)) |
#                     (UserModel.name.ilike(search_term)) |
#                     (UserModel.last_name.ilike(search_term))
#                 )

#             result = await self.session.execute(stmt)
#             users = result.scalars().all()
#             return len(users)
#         except Exception as e:
#             logger.error(f"Error counting users: {e}", exc_info=True)
#             return 0

#     async def list_users(
#         self,
#         status_filter: Optional[str] = None,
#         role_filter: Optional[str] = None,
#         organization_id_filter: Optional[UUID] = None,
#         search_query: Optional[str] = None,
#         limit: int = 50,
#         offset: int = 0,
#     ) -> List[User]:
#         """List users with optional filters and pagination."""
#         try:
#             stmt = select(UserModel)

#             # Apply filters
#             if status_filter:
#                 stmt = stmt.where(UserModel.status == status_filter)

#             if role_filter:
#                 stmt = stmt.where(UserModel.role == role_filter)

#             if organization_id_filter:
#                 stmt = stmt.where(UserModel.organization_id == organization_id_filter)

#             if search_query:
#                 search_term = f"%{search_query}%"
#                 stmt = stmt.where(
#                     (UserModel.email.ilike(search_term)) |
#                     (UserModel.name.ilike(search_term)) |
#                     (UserModel.last_name.ilike(search_term))
#                 )

#             # Apply pagination
#             stmt = stmt.offset(offset).limit(limit)

#             # Order by created_at descending
#             stmt = stmt.order_by(UserModel.created_at.desc())

#             result = await self.session.execute(stmt)
#             user_models = result.scalars().all()

#             return [self._map_model_to_entity(model) for model in user_models]
#         except Exception as e:
#             logger.error(f"Error listing users: {e}", exc_info=True)
#             return []

#     async def count_active_users(self, since_date=None) -> int:
#         """Count active users, optionally since a specific date."""
#         try:
#             stmt = select(UserModel).where(UserModel.status == "active")

#             # If a since_date is provided, filter by last_login_at or created_at
#             if since_date:
#                 stmt = stmt.where(
#                     (UserModel.last_login_at >= since_date) |
#                     (UserModel.created_at >= since_date)
#                 )

#             result = await self.session.execute(stmt)
#             users = result.scalars().all()
#             return len(users)
#         except Exception as e:
#             logger.error(f"Error counting active users: {e}", exc_info=True)
#             return 0

#     async def count_new_users(self, start_date, end_date) -> int:
#         """Count new users created within a specific date range."""
#         try:
#             stmt = select(UserModel).where(
#                 (UserModel.created_at >= start_date) &
#                 (UserModel.created_at <= end_date)
#             )

#             result = await self.session.execute(stmt)
#             users = result.scalars().all()
#             return len(users)
#         except Exception as e:
#             logger.error(f"Error counting new users: {e}", exc_info=True)
#             return 0
