"""
File: base.py
Description: A concise description of the file's purpose and functionality
Author: HappyRobot Team
Created: 2025-05-30
Last Modified: 2025-05-30

Modification History:
- 2025-05-30: Initial file creation

Dependencies:
- List major dependencies or related files
"""

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.sql import func


# Create the base class for declarative models
class Base(DeclarativeBase):
    pass


# Mixin for created_at and updated_at timestamps
class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
