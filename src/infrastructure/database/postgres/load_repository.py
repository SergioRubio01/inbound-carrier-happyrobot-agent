"""
File: load_repository.py
Description: PostgreSQL implementation of load repository
Author: HappyRobot Team
Created: 2024-08-14
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.core.domain.entities import Load, LoadStatus
from src.core.domain.value_objects import EquipmentType, Location, Rate
from src.core.ports.repositories import ILoadRepository, LoadSearchCriteria
from src.infrastructure.database.models import LoadModel
from .base_repository import BaseRepository


class PostgresLoadRepository(BaseRepository[LoadModel, Load], ILoadRepository):
    """PostgreSQL implementation of load repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, LoadModel)

    def _model_to_entity(self, model: LoadModel) -> Load:
        """Convert database model to domain entity."""
        if not model:
            return None

        origin = Location(
            city=model.origin_city,
            state=model.origin_state,
            zip_code=model.origin_zip
        )

        destination = Location(
            city=model.destination_city,
            state=model.destination_state,
            zip_code=model.destination_zip
        )

        equipment_type = EquipmentType.from_name(model.equipment_type)
        loadboard_rate = Rate.from_float(model.loadboard_rate)

        return Load(
            load_id=model.load_id,
            reference_number=model.reference_number,
            origin=origin,
            destination=destination,
            pickup_date=model.pickup_date,
            pickup_time_start=model.pickup_time_start,
            delivery_date=model.delivery_date,
            delivery_time_start=model.delivery_time_start,
            equipment_type=equipment_type,
            weight=model.weight,
            commodity_type=model.commodity_type,
            loadboard_rate=loadboard_rate,
            status=LoadStatus(model.status),
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Load) -> LoadModel:
        """Convert domain entity to database model."""
        return LoadModel(
            load_id=entity.load_id,
            reference_number=entity.reference_number,
            origin_city=entity.origin.city,
            origin_state=entity.origin.state,
            origin_zip=entity.origin.zip_code,
            destination_city=entity.destination.city,
            destination_state=entity.destination.state,
            destination_zip=entity.destination.zip_code,
            pickup_date=entity.pickup_date,
            pickup_time_start=entity.pickup_time_start,
            delivery_date=entity.delivery_date,
            delivery_time_start=entity.delivery_time_start,
            equipment_type=entity.equipment_type.name,
            weight=entity.weight,
            commodity_type=entity.commodity_type,
            loadboard_rate=entity.loadboard_rate.to_float(),
            status=entity.status.value,
            notes=entity.notes,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, load: Load) -> Load:
        """Create a new load."""
        model = self._entity_to_model(load)
        created_model = await super().create(model)
        return self._model_to_entity(created_model)

    async def get_by_id(self, load_id: UUID) -> Optional[Load]:
        """Get load by ID."""
        stmt = select(LoadModel).where(LoadModel.load_id == load_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_active_by_id(self, load_id: UUID) -> Optional[Load]:
        """Get active load by ID."""
        stmt = select(LoadModel).where(
            LoadModel.load_id == load_id,
            LoadModel.is_active
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_reference_number(self, reference_number: str) -> Optional[Load]:
        """Get load by reference number."""
        stmt = select(LoadModel).where(LoadModel.reference_number == reference_number)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(self, load: Load) -> Load:
        """Update existing load."""
        # Get the existing load
        stmt = select(LoadModel).where(LoadModel.load_id == load.load_id)
        result = await self.session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if not existing_model:
            raise Exception(f"Load not found. Load ID: {load.load_id}")

        # Update the existing model directly with the new values
        existing_model.origin_city = load.origin.city
        existing_model.origin_state = load.origin.state
        existing_model.origin_zip = load.origin.zip_code
        existing_model.destination_city = load.destination.city
        existing_model.destination_state = load.destination.state
        existing_model.destination_zip = load.destination.zip_code
        existing_model.pickup_date = load.pickup_date
        existing_model.pickup_time_start = load.pickup_time_start
        existing_model.delivery_date = load.delivery_date
        existing_model.delivery_time_start = load.delivery_time_start
        existing_model.equipment_type = load.equipment_type.name
        existing_model.loadboard_rate = load.loadboard_rate.to_float()
        existing_model.weight = load.weight
        existing_model.commodity_type = load.commodity_type
        existing_model.notes = load.notes
        existing_model.status = load.status.value
        existing_model.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(existing_model)

        return self._model_to_entity(existing_model)

    async def delete(self, load_id: UUID) -> bool:
        """Delete load (soft delete)."""
        stmt = select(LoadModel).where(LoadModel.load_id == load_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.is_active = False
            model.updated_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False

    async def search_loads(self, criteria: LoadSearchCriteria) -> List[Load]:
        """Search loads by criteria."""
        stmt = select(LoadModel)

        conditions = []

        if criteria.equipment_type:
            conditions.append(LoadModel.equipment_type == criteria.equipment_type.name)
        if criteria.origin_state:
            conditions.append(LoadModel.origin_state == criteria.origin_state)
        if criteria.destination_state:
            conditions.append(LoadModel.destination_state == criteria.destination_state)
        if criteria.pickup_date_start:
            conditions.append(LoadModel.pickup_date >= criteria.pickup_date_start)
        if criteria.pickup_date_end:
            conditions.append(LoadModel.pickup_date <= criteria.pickup_date_end)
        if criteria.minimum_rate:
            conditions.append(LoadModel.loadboard_rate >= criteria.minimum_rate.to_float())
        if criteria.maximum_rate:
            conditions.append(LoadModel.loadboard_rate <= criteria.maximum_rate.to_float())
        if criteria.maximum_miles:
            conditions.append(LoadModel.miles <= criteria.maximum_miles)
        if criteria.weight_min:
            conditions.append(LoadModel.weight >= criteria.weight_min)
        if criteria.weight_max:
            conditions.append(LoadModel.weight <= criteria.weight_max)
        if criteria.status:
            conditions.append(LoadModel.status == criteria.status.value)
        if criteria.is_active:
            conditions.append(LoadModel.is_active)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Add sorting
        if criteria.sort_by:
            order_clause = self._build_order_clause(criteria.sort_by)
            if order_clause is not None:
                stmt = stmt.order_by(order_clause)

        stmt = stmt.limit(criteria.limit).offset(criteria.offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_available_loads(self, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get list of available loads."""
        stmt = (
            select(LoadModel)
            .where(
                and_(
                    LoadModel.status == 'AVAILABLE',
                    LoadModel.is_active
                )
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_loads_by_status(self, status: LoadStatus, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get loads by status."""
        stmt = (
            select(LoadModel)
            .where(LoadModel.status == status.value)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_loads_by_carrier(self, carrier_id: UUID, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get loads booked by specific carrier."""
        # Note: This method is not applicable since we removed carrier booking tracking
        return []

    async def count_loads_by_criteria(self, criteria: LoadSearchCriteria) -> int:
        """Count loads matching criteria."""
        stmt = select(func.count()).select_from(LoadModel)

        conditions = []
        if criteria.equipment_type:
            conditions.append(LoadModel.equipment_type == criteria.equipment_type.name)
        # Add other conditions similar to search_loads...

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_loads_expiring_soon(self, hours: int = 24) -> List[Load]:
        """Get loads expiring within specified hours."""
        # Note: This method is not applicable since we removed expiration tracking
        return []

    async def get_load_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get aggregated load metrics for date range."""
        # Total booked revenue
        total_revenue_stmt = select(func.sum(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.status == 'BOOKED',
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date
            )
        )
        total_revenue_result = await self.session.execute(total_revenue_stmt)
        total_booked_revenue = float(total_revenue_result.scalar() or 0)

        # Average load value (for all loads)
        avg_value_stmt = select(func.avg(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date,
                LoadModel.is_active
            )
        )
        avg_value_result = await self.session.execute(avg_value_stmt)
        average_load_value = float(avg_value_result.scalar() or 0)

        # Average loadboard rate
        avg_rate_stmt = select(func.avg(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date,
                LoadModel.is_active
            )
        )
        avg_rate_result = await self.session.execute(avg_rate_stmt)
        average_loadboard_rate = float(avg_rate_result.scalar() or 0)

        return {
            'total_booked_revenue': total_booked_revenue,
            'average_load_value': average_load_value,
            'average_loadboard_rate': average_loadboard_rate
        }

    async def list_all(self,
                      status: Optional[LoadStatus] = None,
                      equipment_type: Optional[str] = None,
                      start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      limit: int = 20,
                      offset: int = 0,
                      sort_by: str = "created_at_desc") -> tuple[List[Load], int]:
        """List all loads with filters and return total count."""
        # Build query with filters
        stmt = select(LoadModel).where(LoadModel.is_active)
        count_stmt = select(func.count()).select_from(LoadModel).where(LoadModel.is_active)

        conditions = []

        if status:
            conditions.append(LoadModel.status == status.value)

        if equipment_type:
            conditions.append(LoadModel.equipment_type == equipment_type)

        if start_date:
            conditions.append(LoadModel.pickup_date >= start_date)

        if end_date:
            conditions.append(LoadModel.pickup_date <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Get total count
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar()

        # Apply sorting
        order_clause = self._build_order_clause(sort_by)
        if order_clause is not None:
            stmt = stmt.order_by(order_clause)
        else:
            # Default sort by created_at desc
            stmt = stmt.order_by(LoadModel.created_at.desc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        loads = [self._model_to_entity(model) for model in models]

        return loads, total_count

    def _build_order_clause(self, sort_by: str):
        """Build SQLAlchemy order clause from sort string."""
        if sort_by == "created_at_desc":
            return LoadModel.created_at.desc()
        elif sort_by == "created_at_asc":
            return LoadModel.created_at.asc()
        elif sort_by == "pickup_date_desc":
            return LoadModel.pickup_date.desc()
        elif sort_by == "pickup_date_asc":
            return LoadModel.pickup_date.asc()
        elif sort_by == "rate_desc":
            return LoadModel.loadboard_rate.desc()
        elif sort_by == "rate_asc":
            return LoadModel.loadboard_rate.asc()
        elif sort_by == "rate_per_mile_desc":
            return (LoadModel.loadboard_rate / LoadModel.miles).desc()
        elif sort_by == "rate_per_mile_asc":
            return (LoadModel.loadboard_rate / LoadModel.miles).asc()
        else:
            return None
