"""
File: negotiation_repository.py
Description: PostgreSQL implementation of negotiation repository
Author: HappyRobot Team
Created: 2024-08-14
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities import Negotiation, NegotiationStatus, SystemResponse
from src.core.domain.value_objects import MCNumber, Rate
from src.core.ports.repositories import (
    INegotiationRepository,
    NegotiationSearchCriteria,
)
from src.infrastructure.database.models import NegotiationModel

from .base_repository import BaseRepository


class PostgresNegotiationRepository(
    BaseRepository[NegotiationModel, Negotiation], INegotiationRepository
):
    """PostgreSQL implementation of negotiation repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, NegotiationModel)

    def _model_to_entity(
        self, model: Optional[NegotiationModel]
    ) -> Optional[Negotiation]:
        """Convert database model to domain entity."""
        if not model:
            return None

        return Negotiation(
            negotiation_id=model.negotiation_id,
            call_id=model.call_id,
            load_id=model.load_id,
            carrier_id=model.carrier_id,
            mc_number=(
                MCNumber.from_string(model.mc_number) if model.mc_number else None
            ),
            session_id=model.session_id,
            session_start=model.session_start,
            session_end=model.session_end,
            is_active=model.is_active,
            round_number=model.round_number,
            max_rounds=model.max_rounds,
            carrier_offer=Rate.from_float(model.carrier_offer),
            system_response=(
                SystemResponse(model.system_response) if model.system_response else None
            ),
            counter_offer=(
                Rate.from_float(model.counter_offer) if model.counter_offer else None
            ),
            loadboard_rate=Rate.from_float(model.loadboard_rate),
            minimum_acceptable=(
                Rate.from_float(model.minimum_acceptable)
                if model.minimum_acceptable
                else None
            ),
            maximum_acceptable=(
                Rate.from_float(model.maximum_acceptable)
                if model.maximum_acceptable
                else None
            ),
            decision_factors=model.decision_factors,
            message_to_carrier=model.message_to_carrier,
            justification=model.justification,
            final_status=(
                NegotiationStatus(model.final_status) if model.final_status else None
            ),
            agreed_rate=(
                Rate.from_float(model.agreed_rate) if model.agreed_rate else None
            ),
            response_time_seconds=model.response_time_seconds,
            total_duration_seconds=model.total_duration_seconds,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            version=model.version,
        )

    def _entity_to_model(self, entity: Negotiation) -> NegotiationModel:
        """Convert domain entity to database model."""
        return NegotiationModel(
            negotiation_id=entity.negotiation_id,
            call_id=entity.call_id,
            load_id=entity.load_id,
            carrier_id=entity.carrier_id,
            mc_number=str(entity.mc_number) if entity.mc_number else None,
            session_id=entity.session_id,
            session_start=entity.session_start,
            session_end=entity.session_end,
            is_active=entity.is_active,
            round_number=entity.round_number,
            max_rounds=entity.max_rounds,
            carrier_offer=(
                entity.carrier_offer.to_float() if entity.carrier_offer else 0.0
            ),
            system_response=(
                entity.system_response.value if entity.system_response else None
            ),
            counter_offer=(
                entity.counter_offer.to_float() if entity.counter_offer else None
            ),
            loadboard_rate=(
                entity.loadboard_rate.to_float() if entity.loadboard_rate else 0.0
            ),
            minimum_acceptable=(
                entity.minimum_acceptable.to_float()
                if entity.minimum_acceptable
                else None
            ),
            maximum_acceptable=(
                entity.maximum_acceptable.to_float()
                if entity.maximum_acceptable
                else None
            ),
            decision_factors=entity.decision_factors,
            message_to_carrier=entity.message_to_carrier,
            justification=entity.justification,
            final_status=entity.final_status.value if entity.final_status else None,
            agreed_rate=entity.agreed_rate.to_float() if entity.agreed_rate else None,
            response_time_seconds=entity.response_time_seconds,
            total_duration_seconds=entity.total_duration_seconds,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            version=entity.version,
        )

    async def create(self, negotiation: Negotiation) -> Negotiation:  # type: ignore[override]
        """Create a new negotiation."""
        model = self._entity_to_model(negotiation)
        created_model = await super().create(model)
        result = self._model_to_entity(created_model)
        if result is None:
            raise RuntimeError("Failed to create negotiation")
        return result

    async def get_by_id(self, negotiation_id: UUID) -> Optional[Negotiation]:  # type: ignore[override]
        """Get negotiation by ID."""
        stmt = select(NegotiationModel).where(
            NegotiationModel.negotiation_id == negotiation_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_session_id(self, session_id: str) -> Optional[Negotiation]:
        """Get active negotiation by session ID."""
        stmt = (
            select(NegotiationModel)
            .where(
                and_(
                    NegotiationModel.session_id == session_id,
                    NegotiationModel.is_active.is_(True),
                )
            )
            .order_by(NegotiationModel.created_at.desc())
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(self, negotiation: Negotiation) -> Negotiation:  # type: ignore[override]
        """Update existing negotiation."""
        model = self._entity_to_model(negotiation)
        model.updated_at = datetime.now(timezone.utc)
        model.version += 1
        updated_model = await super().update(model)
        result = self._model_to_entity(updated_model)
        if result is None:
            raise RuntimeError("Failed to update negotiation")
        return result

    async def delete(self, negotiation_id: UUID) -> bool:
        """Delete negotiation."""
        return await super().delete(negotiation_id)

    async def search_negotiations(
        self, criteria: NegotiationSearchCriteria
    ) -> List[Negotiation]:
        """Search negotiations by criteria."""
        stmt = select(NegotiationModel)

        conditions = []

        if criteria.call_id:
            conditions.append(NegotiationModel.call_id == criteria.call_id)
        if criteria.load_id:
            conditions.append(NegotiationModel.load_id == criteria.load_id)
        if criteria.carrier_id:
            conditions.append(NegotiationModel.carrier_id == criteria.carrier_id)
        if criteria.mc_number:
            conditions.append(NegotiationModel.mc_number == str(criteria.mc_number))
        if criteria.session_id:
            conditions.append(NegotiationModel.session_id == criteria.session_id)
        if criteria.is_active is not None:
            conditions.append(NegotiationModel.is_active == criteria.is_active)
        if criteria.final_status:
            conditions.append(
                NegotiationModel.final_status == criteria.final_status.value
            )
        if criteria.start_date:
            conditions.append(NegotiationModel.session_start >= criteria.start_date)
        if criteria.end_date:
            conditions.append(NegotiationModel.session_start <= criteria.end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.limit(criteria.limit).offset(criteria.offset)
        stmt = stmt.order_by(NegotiationModel.session_start.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]

    async def get_negotiations_by_call(self, call_id: UUID) -> List[Negotiation]:
        """Get all negotiations for a specific call."""
        stmt = (
            select(NegotiationModel)
            .where(NegotiationModel.call_id == call_id)
            .order_by(NegotiationModel.round_number.asc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]

    async def get_negotiations_by_load(
        self, load_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Negotiation]:
        """Get negotiations for a specific load."""
        stmt = (
            select(NegotiationModel)
            .where(NegotiationModel.load_id == load_id)
            .limit(limit)
            .offset(offset)
            .order_by(NegotiationModel.session_start.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]

    async def get_active_negotiations(
        self, limit: int = 100, offset: int = 0
    ) -> List[Negotiation]:
        """Get currently active negotiations."""
        stmt = (
            select(NegotiationModel)
            .where(NegotiationModel.is_active.is_(True))  # noqa: E712
            .limit(limit)
            .offset(offset)
            .order_by(NegotiationModel.session_start.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]

    async def get_negotiations_by_status(
        self, status: NegotiationStatus, limit: int = 100, offset: int = 0
    ) -> List[Negotiation]:
        """Get negotiations by final status."""
        stmt = (
            select(NegotiationModel)
            .where(NegotiationModel.final_status == status.value)
            .limit(limit)
            .offset(offset)
            .order_by(NegotiationModel.session_start.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]

    async def get_negotiation_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated negotiation metrics for date range."""
        # Total negotiations
        total_negotiations_stmt = select(func.count()).where(
            and_(
                NegotiationModel.session_start >= start_date,
                NegotiationModel.session_start <= end_date,
            )
        )
        total_negotiations_result = await self.session.execute(total_negotiations_stmt)
        total_negotiations = total_negotiations_result.scalar()

        # Negotiations by status
        status_stmt = (
            select(NegotiationModel.final_status, func.count().label("count"))
            .where(
                and_(
                    NegotiationModel.session_start >= start_date,
                    NegotiationModel.session_start <= end_date,
                    NegotiationModel.final_status.isnot(None),
                )
            )
            .group_by(NegotiationModel.final_status)
        )

        status_result = await self.session.execute(status_stmt)
        statuses = {row.final_status: row.count for row in status_result}

        # Average negotiation rounds
        avg_rounds_stmt = select(func.avg(NegotiationModel.round_number)).where(
            and_(
                NegotiationModel.session_start >= start_date,
                NegotiationModel.session_start <= end_date,
            )
        )
        avg_rounds_result = await self.session.execute(avg_rounds_stmt)
        avg_rounds = avg_rounds_result.scalar() or 0

        # Success rate (deal accepted)
        success_stmt = select(func.count()).where(
            and_(
                NegotiationModel.session_start >= start_date,
                NegotiationModel.session_start <= end_date,
                NegotiationModel.final_status == "DEAL_ACCEPTED",
            )
        )
        success_result = await self.session.execute(success_stmt)
        successful_negotiations = success_result.scalar()

        success_rate = (
            ((successful_negotiations or 0) / total_negotiations * 100)
            if total_negotiations is not None and total_negotiations > 0
            else 0
        )

        return {
            "total_negotiations": total_negotiations,
            "statuses": statuses,
            "average_rounds": round(avg_rounds, 2) if avg_rounds else 0,
            "success_rate_percent": round(success_rate, 2),
            "successful_negotiations": successful_negotiations,
        }

    async def count_negotiations_by_criteria(
        self, criteria: NegotiationSearchCriteria
    ) -> int:
        """Count negotiations matching criteria."""
        stmt = select(func.count(NegotiationModel.negotiation_id))

        conditions = []
        if criteria.call_id:
            conditions.append(NegotiationModel.call_id == criteria.call_id)
        if criteria.load_id:
            conditions.append(NegotiationModel.load_id == criteria.load_id)
        if criteria.carrier_id:
            conditions.append(NegotiationModel.carrier_id == criteria.carrier_id)
        if criteria.mc_number:
            conditions.append(NegotiationModel.mc_number == str(criteria.mc_number))
        if criteria.session_id:
            conditions.append(NegotiationModel.session_id == criteria.session_id)
        if criteria.is_active is not None:
            conditions.append(NegotiationModel.is_active == criteria.is_active)
        if criteria.final_status:
            conditions.append(
                NegotiationModel.final_status == criteria.final_status.value
            )
        if criteria.start_date:
            conditions.append(NegotiationModel.session_start >= criteria.start_date)
        if criteria.end_date:
            conditions.append(NegotiationModel.session_start <= criteria.end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def get_carrier_negotiation_history(
        self, carrier_id: UUID, limit: int = 50
    ) -> List[Negotiation]:
        """Get negotiation history for a specific carrier."""
        stmt = (
            select(NegotiationModel)
            .where(NegotiationModel.carrier_id == carrier_id)
            .limit(limit)
            .order_by(NegotiationModel.session_start.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [self._model_to_entity(model) for model in models]
        return [e for e in entities if e is not None]
