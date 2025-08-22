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
        response_reason: Optional[str] = None,
        sentiment: Optional[str] = None,
        sentiment_reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> CallMetricsModel:
        """Create new call metrics record."""
        metrics = CallMetricsModel(
            transcript=transcript,
            response=response,
            response_reason=response_reason,
            sentiment=sentiment,
            sentiment_reason=sentiment_reason,
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

        # Calculate success rate
        success_count = response_distribution.get("Success", 0)
        success_rate = (success_count / total_calls) if total_calls > 0 else 0.0

        # Get sentiment distribution
        sentiment_stmt = select(
            CallMetricsModel.sentiment, func.count(CallMetricsModel.sentiment)
        ).group_by(CallMetricsModel.sentiment)
        if base_filter is not None:
            sentiment_stmt = sentiment_stmt.where(base_filter)
        sentiment_result = await self.session.execute(sentiment_stmt)
        sentiment_distribution = {
            sentiment: count
            for sentiment, count in sentiment_result.fetchall()
            if sentiment
        }

        # Top response reasons (for non-success responses)
        response_reasons_stmt = (
            select(
                CallMetricsModel.response_reason,
                func.count(CallMetricsModel.response_reason),
            )
            .where(
                CallMetricsModel.response != "Success",
                CallMetricsModel.response_reason.is_not(None),
            )
            .group_by(CallMetricsModel.response_reason)
            .order_by(desc(func.count(CallMetricsModel.response_reason)))
            .limit(10)
        )
        if base_filter is not None:
            response_reasons_stmt = response_reasons_stmt.where(base_filter)
        response_result = await self.session.execute(response_reasons_stmt)
        top_response_reasons = [
            {"reason": reason, "count": count}
            for reason, count in response_result.fetchall()
        ]

        # Top sentiment reasons (for negative sentiment)
        sentiment_reasons_stmt = (
            select(
                CallMetricsModel.sentiment_reason,
                func.count(CallMetricsModel.sentiment_reason),
            )
            .where(
                CallMetricsModel.sentiment == "Negative",
                CallMetricsModel.sentiment_reason.is_not(None),
            )
            .group_by(CallMetricsModel.sentiment_reason)
            .order_by(desc(func.count(CallMetricsModel.sentiment_reason)))
            .limit(10)
        )
        if base_filter is not None:
            sentiment_reasons_stmt = sentiment_reasons_stmt.where(base_filter)
        sentiment_result = await self.session.execute(sentiment_reasons_stmt)
        top_sentiment_reasons = [
            {"reason": reason, "count": count}
            for reason, count in sentiment_result.fetchall()
        ]

        return {
            "total_calls": total_calls,
            "success_rate": round(success_rate, 4),
            "sentiment_distribution": sentiment_distribution,
            "response_distribution": response_distribution,
            "top_response_reasons": top_response_reasons,
            "top_sentiment_reasons": top_sentiment_reasons,
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
