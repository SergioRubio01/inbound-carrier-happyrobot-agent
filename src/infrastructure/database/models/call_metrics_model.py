"""
File: call_metrics_model.py
Description: SQLAlchemy model for call metrics storage
Author: HappyRobot Team
Created: 2025-01-08
Updated: 2025-08-22 - Phase 1 metrics improvements
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class CallMetricsModel(Base, TimestampMixin):
    """SQLAlchemy model for call_metrics table."""

    __tablename__ = "call_metrics"

    # Primary Key
    metrics_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core Fields
    transcript = Column(Text, nullable=False)
    response = Column(
        String(50), nullable=False
    )  # "Success", "Rate too high", "Incorrect MC", "Fallback error"
    response_reason = Column(Text, nullable=True)
    sentiment = Column(
        Enum("Positive", "Neutral", "Negative", name="sentiment_enum"), nullable=True
    )
    sentiment_reason = Column(Text, nullable=True)

    # Metadata
    session_id = Column(String(100), nullable=True, index=True)

    # Add indexes for commonly queried fields
    __table_args__ = (
        Index("idx_call_metrics_session_id", "session_id"),
        Index("idx_call_metrics_response", "response"),
        Index("idx_call_metrics_sentiment", "sentiment"),
        Index("idx_call_metrics_created_at", "created_at"),
        Index("idx_call_metrics_response_created_at", "response", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CallMetricsModel(metrics_id='{self.metrics_id}', response='{self.response}', session_id='{self.session_id}')>"
