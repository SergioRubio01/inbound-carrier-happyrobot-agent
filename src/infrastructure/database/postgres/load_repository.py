"""
File: load_repository.py
Description: PostgreSQL implementation of load repository
Author: HappyRobot Team
Created: 2024-08-14
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities import Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, Rate
from src.core.ports.repositories import ILoadRepository, LoadSearchCriteria
from src.infrastructure.database.models import LoadModel

from .base_repository import BaseRepository


class PostgresLoadRepository(BaseRepository[LoadModel, Load], ILoadRepository):
    """PostgreSQL implementation of load repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, LoadModel)

    def _model_to_entity(self, model: Optional[LoadModel]) -> Optional[Load]:
        """Convert database model to domain entity."""
        if not model:
            return None

        origin = Location(
            city=model.origin_city, state=model.origin_state, zip_code=model.origin_zip
        )

        destination = Location(
            city=model.destination_city,
            state=model.destination_state,
            zip_code=model.destination_zip,
        )

        equipment_type = EquipmentType.from_name(model.equipment_type)
        loadboard_rate = Rate.from_float(model.loadboard_rate)
        fuel_surcharge = (
            Rate.from_float(model.fuel_surcharge) if model.fuel_surcharge else None
        )

        return Load(
            load_id=model.load_id,
            reference_number=model.reference_number,
            external_id=model.external_id,
            origin=origin,
            destination=destination,
            pickup_date=model.pickup_date,
            pickup_time_start=model.pickup_time_start,
            pickup_time_end=model.pickup_time_end,
            pickup_appointment_required=model.pickup_appointment_required,
            delivery_date=model.delivery_date,
            delivery_time_start=model.delivery_time_start,
            delivery_time_end=model.delivery_time_end,
            delivery_appointment_required=model.delivery_appointment_required,
            equipment_type=equipment_type,
            equipment_requirements=model.equipment_requirements,
            weight=model.weight,
            pieces=model.pieces,
            commodity_type=model.commodity_type,
            commodity_description=model.commodity_description,
            dimensions=model.dimensions,
            hazmat=model.hazmat,
            hazmat_class=model.hazmat_class,
            miles=model.miles,
            estimated_transit_hours=model.estimated_transit_hours,
            route_notes=model.route_notes,
            loadboard_rate=loadboard_rate,
            fuel_surcharge=fuel_surcharge,
            accessorials=model.accessorials,
            minimum_rate=(
                Rate.from_float(model.minimum_rate) if model.minimum_rate else None
            ),
            maximum_rate=(
                Rate.from_float(model.maximum_rate) if model.maximum_rate else None
            ),
            target_rate=(
                Rate.from_float(model.target_rate) if model.target_rate else None
            ),
            auto_accept_threshold=(
                Rate.from_float(model.auto_accept_threshold)
                if model.auto_accept_threshold
                else None
            ),
            broker_company=model.broker_company,
            broker_contact=model.broker_contact,
            customer_name=model.customer_name,
            status=LoadStatus(model.status),
            status_changed_at=model.status_changed_at,
            booked_by_carrier_id=model.booked_by_carrier_id,
            booked_at=model.booked_at,
            special_requirements=model.special_requirements,
            notes=model.notes,
            internal_notes=model.internal_notes,
            urgency=UrgencyLevel(model.urgency),
            priority_score=model.priority_score,
            is_active=model.is_active,
            expires_at=model.expires_at,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            deleted_at=model.deleted_at,
            version=model.version,
        )

    def _entity_to_model(self, entity: Load) -> LoadModel:
        """Convert domain entity to database model."""
        return LoadModel(
            load_id=entity.load_id,
            reference_number=entity.reference_number,
            external_id=entity.external_id,
            origin_city=entity.origin.city if entity.origin else None,
            origin_state=entity.origin.state if entity.origin else None,
            origin_zip=entity.origin.zip_code if entity.origin else None,
            destination_city=entity.destination.city if entity.destination else None,
            destination_state=entity.destination.state if entity.destination else None,
            destination_zip=entity.destination.zip_code if entity.destination else None,
            pickup_date=entity.pickup_date,
            pickup_time_start=entity.pickup_time_start,
            pickup_time_end=entity.pickup_time_end,
            pickup_appointment_required=entity.pickup_appointment_required,
            delivery_date=entity.delivery_date,
            delivery_time_start=entity.delivery_time_start,
            delivery_time_end=entity.delivery_time_end,
            delivery_appointment_required=entity.delivery_appointment_required,
            equipment_type=(
                entity.equipment_type.name if entity.equipment_type else None
            ),
            equipment_requirements=entity.equipment_requirements,
            weight=entity.weight,
            pieces=entity.pieces,
            commodity_type=entity.commodity_type,
            commodity_description=entity.commodity_description,
            dimensions=entity.dimensions,
            hazmat=entity.hazmat,
            hazmat_class=entity.hazmat_class,
            miles=entity.miles,
            estimated_transit_hours=entity.estimated_transit_hours,
            route_notes=entity.route_notes,
            loadboard_rate=(
                entity.loadboard_rate.to_float() if entity.loadboard_rate else 0.0
            ),
            fuel_surcharge=(
                entity.fuel_surcharge.to_float() if entity.fuel_surcharge else 0
            ),
            accessorials=entity.accessorials,
            minimum_rate=(
                entity.minimum_rate.to_float() if entity.minimum_rate else None
            ),
            maximum_rate=(
                entity.maximum_rate.to_float() if entity.maximum_rate else None
            ),
            target_rate=entity.target_rate.to_float() if entity.target_rate else None,
            auto_accept_threshold=(
                entity.auto_accept_threshold.to_float()
                if entity.auto_accept_threshold
                else None
            ),
            broker_company=entity.broker_company,
            broker_contact=entity.broker_contact,
            customer_name=entity.customer_name,
            status=entity.status.value,
            status_changed_at=entity.status_changed_at,
            booked_by_carrier_id=entity.booked_by_carrier_id,
            booked_at=entity.booked_at,
            special_requirements=entity.special_requirements,
            notes=entity.notes,
            internal_notes=entity.internal_notes,
            urgency=entity.urgency.value,
            priority_score=entity.priority_score,
            is_active=entity.is_active,
            expires_at=entity.expires_at,
            source=entity.source,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            deleted_at=entity.deleted_at,
            version=entity.version,
        )

    async def create(self, load: Load) -> Load:  # type: ignore[override]
        """Create a new load."""
        model = self._entity_to_model(load)
        created_model = await super().create(model)
        return self._model_to_entity(created_model)

    async def get_by_id(self, load_id: UUID) -> Optional[Load]:  # type: ignore[override]
        """Get load by ID."""
        stmt = select(LoadModel).where(LoadModel.load_id == load_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_reference_number(self, reference_number: str) -> Optional[Load]:
        """Get load by reference number."""
        stmt = select(LoadModel).where(LoadModel.reference_number == reference_number)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(self, load: Load) -> Load:  # type: ignore[override]
        """Update existing load."""
        model = self._entity_to_model(load)
        model.updated_at = datetime.utcnow()
        model.version += 1
        updated_model = await super().update(model)
        return self._model_to_entity(updated_model)

    async def delete(self, load_id: UUID) -> bool:
        """Delete load (soft delete)."""
        stmt = select(LoadModel).where(LoadModel.load_id == load_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.deleted_at = datetime.utcnow()
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
            conditions.append(
                LoadModel.loadboard_rate >= criteria.minimum_rate.to_float()
            )
        if criteria.maximum_rate:
            conditions.append(
                LoadModel.loadboard_rate <= criteria.maximum_rate.to_float()
            )
        if criteria.maximum_miles:
            conditions.append(LoadModel.miles <= criteria.maximum_miles)
        if criteria.weight_min:
            conditions.append(LoadModel.weight >= criteria.weight_min)
        if criteria.weight_max:
            conditions.append(LoadModel.weight <= criteria.weight_max)
        if criteria.status:
            conditions.append(LoadModel.status == criteria.status.value)
        if criteria.is_active:
            conditions.append(LoadModel.is_active is True)
            conditions.append(LoadModel.deleted_at.is_(None))

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

    async def get_available_loads(
        self, limit: int = 100, offset: int = 0
    ) -> List[Load]:
        """Get list of available loads."""
        stmt = (
            select(LoadModel)
            .where(
                and_(
                    LoadModel.status == "AVAILABLE",
                    LoadModel.is_active is True,
                    LoadModel.deleted_at.is_(None),
                )
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_loads_by_status(
        self, status: LoadStatus, limit: int = 100, offset: int = 0
    ) -> List[Load]:
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

    async def get_loads_by_carrier(
        self, carrier_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Load]:
        """Get loads booked by specific carrier."""
        stmt = (
            select(LoadModel)
            .where(LoadModel.booked_by_carrier_id == carrier_id)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

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
        return int(result.scalar() or 0)

    async def get_loads_expiring_soon(self, hours: int = 24) -> List[Load]:
        """Get loads expiring within specified hours."""
        from sqlalchemy import text

        stmt = select(LoadModel).where(
            and_(
                LoadModel.expires_at.isnot(None),
                LoadModel.expires_at <= text(f"NOW() + INTERVAL '{hours} hours'"),
                LoadModel.status == "AVAILABLE",
                LoadModel.is_active is True,
            )
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_load_metrics(  # type: ignore[override]
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated load metrics for date range."""
        # Total booked revenue
        total_revenue_stmt = select(func.sum(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.status == "BOOKED",
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date,
            )
        )
        total_revenue_result = await self.session.execute(total_revenue_stmt)
        total_booked_revenue = float(total_revenue_result.scalar() or 0)

        # Average load value (for all loads)
        avg_value_stmt = select(func.avg(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date,
                LoadModel.is_active is True,
            )
        )
        avg_value_result = await self.session.execute(avg_value_stmt)
        average_load_value = float(avg_value_result.scalar() or 0)

        # Average loadboard rate
        avg_rate_stmt = select(func.avg(LoadModel.loadboard_rate)).where(
            and_(
                LoadModel.created_at >= start_date,
                LoadModel.created_at <= end_date,
                LoadModel.is_active is True,
            )
        )
        avg_rate_result = await self.session.execute(avg_rate_stmt)
        average_loadboard_rate = float(avg_rate_result.scalar() or 0)

        return {
            "total_booked_revenue": total_booked_revenue,
            "average_load_value": average_load_value,
            "average_loadboard_rate": average_loadboard_rate,
        }
