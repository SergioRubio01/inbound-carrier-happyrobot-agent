# import uuid
# from datetime import datetime
# from typing import TYPE_CHECKING, List, Optional

# from sqlalchemy import JSON, UUID, Boolean, DateTime, ForeignKey, String, Text
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.sql import func

# from HappyRobot.core.domain.entities.user import UserStatus
# from HappyRobot.infrastructure.database.base import Base

# if TYPE_CHECKING:
#     # Assuming NotificationModel is needed for a notifications relationship
#     from .audit_log_model import AuditLogModel
#     from .integration_model import IntegrationModel
#     from .invitation_model import InvitationModel
#     from .notification_model import NotificationModel
#     from .oauth_account_model import OAuthAccountModel
#     from .organization_model import OrganizationModel


# class UserModel(Base):
#     """SQLAlchemy model for the User entity"""

#     __tablename__ = "users"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     # Field to store the ID of the user's organization
#     organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("organizations.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True,
#     )
#     # Field to store the invitation that created this user
#     invitation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("invitations.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True,
#     )
#     email: Mapped[str] = mapped_column(
#         String(255), unique=True, nullable=False, index=True
#     )
#     hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
#     name: Mapped[str] = mapped_column(String(255), nullable=False)
#     last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
#     status: Mapped[str] = mapped_column(
#         String(50), nullable=False, default=UserStatus.ACTIVE.value, index=True
#     )
#     role: Mapped[str] = mapped_column(
#         String(50), nullable=False, default="member", index=True
#     )
#     is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
#     profile_picture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     avatar_color: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
#     preferences: Mapped[dict] = mapped_column(JSON, default=lambda: {})
#     last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime,
#         nullable=False,
#         default=datetime.utcnow,
#         server_default=func.now(),
#         onupdate=func.now(),
#     )

#     # Relationships
#     # Single organization relationship
#     organization: Mapped[Optional["OrganizationModel"]] = relationship(
#         "OrganizationModel", foreign_keys=[organization_id], back_populates="users"
#     )
#     oauth_accounts: Mapped[List["OAuthAccountModel"]] = relationship(
#         "OAuthAccountModel", back_populates="user", cascade="all, delete-orphan"
#     )
#     # Note: project_memberships and assigned_projects relationships removed
#     # These referenced tables that were dropped in migration remove_project_members_001
#     # Projects use simple creator ownership model via created_projects relationship
#     notifications: Mapped[List["NotificationModel"]] = relationship(
#         "NotificationModel", back_populates="user", cascade="all, delete-orphan"
#     )
#     audit_logs: Mapped[List["AuditLogModel"]] = relationship(
#         "AuditLogModel", back_populates="user", cascade="all, delete-orphan"
#     )
#     sent_invitations: Mapped[List["InvitationModel"]] = relationship(
#         "InvitationModel",
#         foreign_keys="InvitationModel.invited_by_id",
#         back_populates="invited_by"
#     )
#     invitation: Mapped[Optional["InvitationModel"]] = relationship(
#         "InvitationModel",
#         foreign_keys="UserModel.invitation_id",
#         back_populates="accepted_by",
#         uselist=False
#     )

#     # Integration relationships
#     created_integrations: Mapped[List["IntegrationModel"]] = relationship(
#         "IntegrationModel",
#         foreign_keys="IntegrationModel.created_by",
#         back_populates="created_by_user"
#     )

#     updated_integrations: Mapped[List["IntegrationModel"]] = relationship(
#         "IntegrationModel",
#         foreign_keys="IntegrationModel.updated_by",
#         back_populates="updated_by_user"
#     )

#     def __repr__(self):
#         return f"<User {self.id} {self.email}>"


# # Add alias for backward compatibility with migrations
# User = UserModel
