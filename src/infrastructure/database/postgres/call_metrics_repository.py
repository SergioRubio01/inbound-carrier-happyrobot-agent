"""
File: call_metrics_repository.py
Description: PostgreSQL implementation of call metrics repository
Author: HappyRobot Team
Created: 2025-01-08
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.call_metrics_model import CallMetricsModel

from .base_repository import BaseRepository


class PostgresCallMetricsRepository(BaseRepository[CallMetricsModel, CallMetricsModel]):
    """PostgreSQL implementation of call metrics repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CallMetricsModel)

    async def create_metrics(
        self,
        transcript: str,
        response: str,
        reason: Optional[str] = None,
        final_loadboard_rate: Optional[float] = None,
        session_id: Optional[str] = None,
    ) -> CallMetricsModel:
        """Create new call metrics record."""
        metrics = CallMetricsModel(
            transcript=transcript,
            response=response,
            reason=reason,
            final_loadboard_rate=final_loadboard_rate,
            session_id=session_id,
        )
        return await self.create(metrics)

    async def get_metrics_by_id(self, metrics_id: UUID) -> Optional[CallMetricsModel]:
        """Get call metrics by ID."""
        stmt = select(CallMetricsModel).where(CallMetricsModel.metrics_id == metrics_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CallMetricsModel]:
        """Get call metrics with optional date filtering."""
        stmt = select(CallMetricsModel)

        conditions = []
        if start_date:
            conditions.append(CallMetricsModel.created_at >= start_date)
        if end_date:
            conditions.append(CallMetricsModel.created_at <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by created_at descending
        stmt = stmt.order_by(desc(CallMetricsModel.created_at))

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_metrics_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregated metrics summary for date range."""
        # Base query conditions
        conditions = []
        if start_date:
            conditions.append(CallMetricsModel.created_at >= start_date)
        if end_date:
            conditions.append(CallMetricsModel.created_at <= end_date)

        base_filter = and_(*conditions) if conditions else None

        # Total calls
        total_stmt = select(func.count(CallMetricsModel.metrics_id))
        if base_filter is not None:
            total_stmt = total_stmt.where(base_filter)
        total_result = await self.session.execute(total_stmt)
        total_calls = int(total_result.scalar() or 0)

        # Response distribution
        response_stmt = select(
            CallMetricsModel.response, func.count(CallMetricsModel.response)
        ).group_by(CallMetricsModel.response)
        if base_filter is not None:
            response_stmt = response_stmt.where(base_filter)
        response_result = await self.session.execute(response_stmt)
        response_distribution = {
            response: count for response, count in response_result.fetchall()
        }

        # Calculate acceptance rate
        accepted_count = response_distribution.get("ACCEPTED", 0)
        acceptance_rate = (accepted_count / total_calls) if total_calls > 0 else 0.0

        # Average final loadboard rate (only for accepted calls)
        avg_rate_stmt = select(func.avg(CallMetricsModel.final_loadboard_rate)).where(
            CallMetricsModel.response == "ACCEPTED",
            CallMetricsModel.final_loadboard_rate.is_not(None),
        )
        if base_filter is not None:
            avg_rate_stmt = avg_rate_stmt.where(base_filter)
        avg_rate_result = await self.session.execute(avg_rate_stmt)
        average_final_rate = float(avg_rate_result.scalar() or 0.0)

        # Top rejection reasons (for rejected calls)
        rejection_reasons_stmt = (
            select(CallMetricsModel.reason, func.count(CallMetricsModel.reason))
            .where(
                CallMetricsModel.response == "REJECTED",
                CallMetricsModel.reason.is_not(None),
            )
            .group_by(CallMetricsModel.reason)
            .order_by(desc(func.count(CallMetricsModel.reason)))
            .limit(10)
        )
        if base_filter is not None:
            rejection_reasons_stmt = rejection_reasons_stmt.where(base_filter)
        rejection_result = await self.session.execute(rejection_reasons_stmt)
        top_rejection_reasons = [
            {"reason": reason, "count": count}
            for reason, count in rejection_result.fetchall()
        ]

        return {
            "total_calls": total_calls,
            "acceptance_rate": round(acceptance_rate, 4),
            "average_final_rate": round(average_final_rate, 2),
            "response_distribution": response_distribution,
            "top_rejection_reasons": top_rejection_reasons,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    async def get_by_id(self, record_id: UUID) -> Optional[CallMetricsModel]:  # type: ignore[override]
        """Get call metrics by ID (implements base class method)."""
        return await self.get_metrics_by_id(record_id)

    async def delete(self, record_id: UUID) -> bool:  # type: ignore[override]
        """Delete call metrics by ID."""
        stmt = select(CallMetricsModel).where(CallMetricsModel.metrics_id == record_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, record_id: UUID) -> bool:  # type: ignore[override]
        """Check if call metrics exists by ID."""
        stmt = select(func.count(CallMetricsModel.metrics_id)).where(
            CallMetricsModel.metrics_id == record_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0) > 0

    async def get_metrics_by_session_id(
        self, session_id: str
    ) -> List[CallMetricsModel]:
        """Get all metrics for a specific session."""
        stmt = (
            select(CallMetricsModel)
            .where(CallMetricsModel.session_id == session_id)
            .order_by(desc(CallMetricsModel.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count metrics with optional date filtering."""
        stmt = select(func.count(CallMetricsModel.metrics_id))

        conditions = []
        if start_date:
            conditions.append(CallMetricsModel.created_at >= start_date)
        if end_date:
            conditions.append(CallMetricsModel.created_at <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
