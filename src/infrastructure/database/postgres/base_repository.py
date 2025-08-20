"""
File: base_repository.py
Description: Base repository implementation for PostgreSQL
Author: HappyRobot Team
Created: 2024-08-14
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.base import Base

T = TypeVar("T", bound=Base)
D = TypeVar("D")  # Domain entity type


class BaseRepository(Generic[T, D]):
    """Base repository for PostgreSQL operations."""

    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def create(self, model: T) -> T:
        """Create a new record."""
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def get_by_id(self, record_id: UUID) -> Optional[T]:
        """Get record by ID."""
        stmt = select(self.model_class).where(self.model_class.id == record_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[return-value]

    async def update(self, model: T) -> T:
        """Update existing record."""
        await self.session.merge(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def delete(self, record_id: UUID) -> bool:
        """Delete record by ID."""
        stmt = delete(self.model_class).where(self.model_class.id == record_id)
        result = await self.session.execute(stmt)
        return bool(result.rowcount > 0)  # type: ignore[attr-defined]

    async def exists(self, record_id: UUID) -> bool:
        """Check if record exists."""
        stmt = select(func.count()).where(self.model_class.id == record_id)
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        return bool(count > 0)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all records with pagination."""
        stmt = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())  # type: ignore[arg-type]

    async def count_all(self) -> int:
        """Count all records."""
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    def _build_where_clause(self, filters: Dict[str, Any]):
        """Build WHERE clause from filters dictionary."""
        conditions = []

        for field, value in filters.items():
            if value is None:
                continue

            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)

                if isinstance(value, dict):
                    # Handle operators like {'>=': 100}, {'like': '%pattern%'}
                    for operator, operand in value.items():
                        if operator == "like":
                            conditions.append(column.like(operand))
                        elif operator == "ilike":
                            conditions.append(column.ilike(operand))
                        elif operator == "in":
                            conditions.append(column.in_(operand))
                        elif operator == "not_in":
                            conditions.append(~column.in_(operand))
                        elif operator == ">":
                            conditions.append(column > operand)
                        elif operator == ">=":
                            conditions.append(column >= operand)
                        elif operator == "<":
                            conditions.append(column < operand)
                        elif operator == "<=":
                            conditions.append(column <= operand)
                        elif operator == "!=":
                            conditions.append(column != operand)
                elif isinstance(value, list):
                    conditions.append(column.in_(value))
                else:
                    conditions.append(column == value)

        return and_(*conditions) if conditions else None

    def _build_order_clause(self, sort_by: Optional[str] = None):
        """Build ORDER BY clause."""
        if not sort_by:
            return None

        # Handle format like "field_name_desc" or "field_name_asc"
        if sort_by.endswith("_desc"):
            field_name = sort_by[:-5]
            direction = desc
        elif sort_by.endswith("_asc"):
            field_name = sort_by[:-4]
            direction = asc
        else:
            field_name = sort_by
            direction = asc

        if hasattr(self.model_class, field_name):
            column = getattr(self.model_class, field_name)
            return direction(column)

        return None
