"""
File: call_repository.py
Description: PostgreSQL implementation of call repository
Author: HappyRobot Team
Created: 2024-08-14
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.core.domain.entities import Call, CallOutcome, Sentiment
from src.core.domain.value_objects import MCNumber
from src.core.ports.repositories import ICallRepository, CallSearchCriteria
from src.infrastructure.database.models import CallModel
from .base_repository import BaseRepository


class PostgresCallRepository(BaseRepository[CallModel, Call], ICallRepository):
    """PostgreSQL implementation of call repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CallModel)

    def _model_to_entity(self, model: CallModel) -> Call:
        """Convert database model to domain entity."""
        if not model:
            return None

        return Call(
            call_id=model.call_id,
            external_call_id=model.external_call_id,
            session_id=model.session_id,
            mc_number=MCNumber.from_string(model.mc_number)
            if model.mc_number
            else None,
            carrier_id=model.carrier_id,
            caller_phone=model.caller_phone,
            caller_name=model.caller_name,
            load_id=model.load_id,
            multiple_loads_discussed=model.multiple_loads_discussed,
            start_time=model.start_time,
            end_time=model.end_time,
            duration_seconds=model.duration_seconds,
            call_type=model.call_type,
            channel=model.channel,
            agent_type=model.agent_type,
            agent_id=model.agent_id,
            outcome=CallOutcome(model.outcome) if model.outcome else None,
            outcome_confidence=model.outcome_confidence,
            sentiment=Sentiment(model.sentiment) if model.sentiment else None,
            sentiment_score=model.sentiment_score,
            sentiment_breakdown=model.sentiment_breakdown,
            initial_offer=model.initial_offer,
            final_rate=model.final_rate,
            rate_accepted=model.rate_accepted,
            extracted_data=model.extracted_data,
            transcript=model.transcript,
            transcript_summary=model.transcript_summary,
            key_points=model.key_points,
            transferred_to_human=model.transferred_to_human,
            transfer_reason=model.transfer_reason,
            transferred_at=model.transferred_at,
            assigned_rep_id=model.assigned_rep_id,
            follow_up_required=model.follow_up_required,
            follow_up_reason=model.follow_up_reason,
            follow_up_deadline=model.follow_up_deadline,
            follow_up_completed=model.follow_up_completed,
            recording_url=model.recording_url,
            recording_duration_seconds=model.recording_duration_seconds,
            quality_score=model.quality_score,
            quality_issues=model.quality_issues,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            version=model.version,
        )

    def _entity_to_model(self, entity: Call) -> CallModel:
        """Convert domain entity to database model."""
        return CallModel(
            call_id=entity.call_id,
            external_call_id=entity.external_call_id,
            session_id=entity.session_id,
            mc_number=str(entity.mc_number) if entity.mc_number else None,
            carrier_id=entity.carrier_id,
            caller_phone=entity.caller_phone,
            caller_name=entity.caller_name,
            load_id=entity.load_id,
            multiple_loads_discussed=entity.multiple_loads_discussed,
            start_time=entity.start_time,
            end_time=entity.end_time,
            duration_seconds=entity.duration_seconds,
            call_type=entity.call_type,
            channel=entity.channel,
            agent_type=entity.agent_type,
            agent_id=entity.agent_id,
            outcome=entity.outcome.value if entity.outcome else None,
            outcome_confidence=entity.outcome_confidence,
            sentiment=entity.sentiment.value if entity.sentiment else None,
            sentiment_score=entity.sentiment_score,
            sentiment_breakdown=entity.sentiment_breakdown,
            initial_offer=entity.initial_offer,
            final_rate=entity.final_rate,
            rate_accepted=entity.rate_accepted,
            extracted_data=entity.extracted_data,
            transcript=entity.transcript,
            transcript_summary=entity.transcript_summary,
            key_points=entity.key_points,
            transferred_to_human=entity.transferred_to_human,
            transfer_reason=entity.transfer_reason,
            transferred_at=entity.transferred_at,
            assigned_rep_id=entity.assigned_rep_id,
            follow_up_required=entity.follow_up_required,
            follow_up_reason=entity.follow_up_reason,
            follow_up_deadline=entity.follow_up_deadline,
            follow_up_completed=entity.follow_up_completed,
            recording_url=entity.recording_url,
            recording_duration_seconds=entity.recording_duration_seconds,
            quality_score=entity.quality_score,
            quality_issues=entity.quality_issues,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            version=entity.version,
        )

    async def create(self, call: Call) -> Call:
        """Create a new call."""
        model = self._entity_to_model(call)
        created_model = await super().create(model)
        return self._model_to_entity(created_model)

    async def get_by_id(self, call_id: UUID) -> Optional[Call]:
        """Get call by ID."""
        stmt = select(CallModel).where(CallModel.call_id == call_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_external_id(self, external_call_id: str) -> Optional[Call]:
        """Get call by external call ID."""
        stmt = select(CallModel).where(CallModel.external_call_id == external_call_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(self, call: Call) -> Call:
        """Update existing call."""
        model = self._entity_to_model(call)
        model.updated_at = datetime.utcnow()
        model.version += 1
        updated_model = await super().update(model)
        return self._model_to_entity(updated_model)

    async def delete(self, call_id: UUID) -> bool:
        """Delete call."""
        return await super().delete(call_id)

    async def search_calls(self, criteria: CallSearchCriteria) -> List[Call]:
        """Search calls by criteria."""
        stmt = select(CallModel)

        conditions = []

        if criteria.mc_number:
            conditions.append(CallModel.mc_number == str(criteria.mc_number))
        if criteria.carrier_id:
            conditions.append(CallModel.carrier_id == criteria.carrier_id)
        if criteria.load_id:
            conditions.append(CallModel.load_id == criteria.load_id)
        if criteria.outcome:
            conditions.append(CallModel.outcome == criteria.outcome.value)
        if criteria.sentiment:
            conditions.append(CallModel.sentiment == criteria.sentiment.value)
        if criteria.start_date:
            conditions.append(CallModel.start_time >= criteria.start_date)
        if criteria.end_date:
            conditions.append(CallModel.start_time <= criteria.end_date)
        if criteria.transferred_to_human is not None:
            conditions.append(
                CallModel.transferred_to_human == criteria.transferred_to_human
            )
        if criteria.follow_up_required is not None:
            conditions.append(
                CallModel.follow_up_required == criteria.follow_up_required
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.limit(criteria.limit).offset(criteria.offset)
        stmt = stmt.order_by(CallModel.start_time.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_calls_by_carrier(
        self, carrier_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls by carrier."""
        stmt = (
            select(CallModel)
            .where(CallModel.carrier_id == carrier_id)
            .limit(limit)
            .offset(offset)
            .order_by(CallModel.start_time.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_calls_by_outcome(
        self, outcome: CallOutcome, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls by outcome."""
        stmt = (
            select(CallModel)
            .where(CallModel.outcome == outcome.value)
            .limit(limit)
            .offset(offset)
            .order_by(CallModel.start_time.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_calls_requiring_follow_up(
        self, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls that require follow-up."""
        stmt = (
            select(CallModel)
            .where(
                and_(
                    CallModel.follow_up_required is True,
                    CallModel.follow_up_completed is False,
                )
            )
            .limit(limit)
            .offset(offset)
            .order_by(CallModel.follow_up_deadline.asc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_active_calls(self, limit: int = 100, offset: int = 0) -> List[Call]:
        """Get currently active calls."""
        stmt = (
            select(CallModel)
            .where(CallModel.end_time.is_(None))
            .limit(limit)
            .offset(offset)
            .order_by(CallModel.start_time.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_call_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated call metrics for date range."""
        # Total calls
        total_calls_stmt = select(func.count()).where(
            and_(CallModel.start_time >= start_date, CallModel.start_time <= end_date)
        )
        total_calls_result = await self.session.execute(total_calls_stmt)
        total_calls = total_calls_result.scalar()

        # Calls by outcome
        outcomes_stmt = (
            select(CallModel.outcome, func.count().label("count"))
            .where(
                and_(
                    CallModel.start_time >= start_date, CallModel.start_time <= end_date
                )
            )
            .group_by(CallModel.outcome)
        )

        outcomes_result = await self.session.execute(outcomes_stmt)
        outcomes = {row.outcome: row.count for row in outcomes_result}

        # Average duration
        avg_duration_stmt = select(func.avg(CallModel.duration_seconds)).where(
            and_(
                CallModel.start_time >= start_date,
                CallModel.start_time <= end_date,
                CallModel.duration_seconds.isnot(None),
            )
        )
        avg_duration_result = await self.session.execute(avg_duration_stmt)
        avg_duration = avg_duration_result.scalar() or 0

        # Follow-ups required
        follow_ups_stmt = select(func.count()).where(
            and_(
                CallModel.start_time >= start_date,
                CallModel.start_time <= end_date,
                CallModel.follow_up_required is True,
            )
        )
        follow_ups_result = await self.session.execute(follow_ups_stmt)
        follow_ups_required = follow_ups_result.scalar()

        return {
            "total_calls": total_calls,
            "outcomes": outcomes,
            "average_duration_seconds": round(avg_duration, 2) if avg_duration else 0,
            "follow_ups_required": follow_ups_required,
        }

    async def count_calls_by_criteria(self, criteria: CallSearchCriteria) -> int:
        """Count calls matching criteria."""
        stmt = select(func.count()).select_from(CallModel)

        conditions = []
        if criteria.mc_number:
            conditions.append(CallModel.mc_number == str(criteria.mc_number))
        if criteria.carrier_id:
            conditions.append(CallModel.carrier_id == criteria.carrier_id)
        if criteria.load_id:
            conditions.append(CallModel.load_id == criteria.load_id)
        if criteria.outcome:
            conditions.append(CallModel.outcome == criteria.outcome.value)
        if criteria.sentiment:
            conditions.append(CallModel.sentiment == criteria.sentiment.value)
        if criteria.start_date:
            conditions.append(CallModel.start_time >= criteria.start_date)
        if criteria.end_date:
            conditions.append(CallModel.start_time <= criteria.end_date)
        if criteria.transferred_to_human is not None:
            conditions.append(
                CallModel.transferred_to_human == criteria.transferred_to_human
            )
        if criteria.follow_up_required is not None:
            conditions.append(
                CallModel.follow_up_required == criteria.follow_up_required
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar()
