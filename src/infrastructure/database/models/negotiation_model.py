"""
File: negotiation_model.py
Description: SQLAlchemy model for negotiation tracking
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .carrier_model import CarrierModel
    from .load_model import LoadModel


class NegotiationModel(Base, TimestampMixin):
    """SQLAlchemy model for negotiations table."""

    __tablename__ = "negotiations"

    # Primary Key
    negotiation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Association
    load_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loads.load_id"), nullable=False, index=True
    )
    carrier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carriers.carrier_id"), index=True, nullable=True
    )
    mc_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Session Management
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_start: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=func.now()
    )
    session_end: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Negotiation Rounds
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    max_rounds: Mapped[int] = mapped_column(Integer, default=3)

    # Offer Details
    carrier_offer: Mapped[float] = mapped_column(NUMERIC(10, 2), nullable=False)
    system_response: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ACCEPTED, COUNTER_OFFER, REJECTED
    counter_offer: Mapped[Optional[float]] = mapped_column(
        NUMERIC(10, 2), nullable=True
    )

    # Context
    loadboard_rate: Mapped[float] = mapped_column(NUMERIC(10, 2), nullable=False)
    minimum_acceptable: Mapped[Optional[float]] = mapped_column(
        NUMERIC(10, 2), nullable=True
    )
    maximum_acceptable: Mapped[Optional[float]] = mapped_column(
        NUMERIC(10, 2), nullable=True
    )

    # Decision Logic
    decision_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    """
    Structure:
    {
        urgency_level, carrier_history, market_conditions,
        competitor_rates, special_requirements
    }
    """

    # Communication
    message_to_carrier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Result
    final_status: Mapped[Optional[str]] = mapped_column(
        String(30), index=True, nullable=True
    )  # DEAL_ACCEPTED, DEAL_REJECTED, ABANDONED, TIMEOUT
    agreed_rate: Mapped[Optional[float]] = mapped_column(NUMERIC(10, 2), nullable=True)

    # Timing
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    load: Mapped["LoadModel"] = relationship("LoadModel", foreign_keys=[load_id])
    carrier: Mapped["CarrierModel"] = relationship(
        "CarrierModel", foreign_keys=[carrier_id]
    )

    @property
    def offer_difference(self) -> float:
        """Calculate difference between carrier offer and loadboard rate."""
        return float(self.carrier_offer) - float(self.loadboard_rate)

    @property
    def percentage_over(self) -> float:
        """Calculate percentage over loadboard rate."""
        if self.loadboard_rate and float(self.loadboard_rate) > 0:
            return (
                (float(self.carrier_offer) - float(self.loadboard_rate))
                / float(self.loadboard_rate)
            ) * 100
        return 0.0

    def __repr__(self) -> str:
        return f"<NegotiationModel(negotiation_id='{self.negotiation_id}', round={self.round_number}, response='{self.system_response}')>"
