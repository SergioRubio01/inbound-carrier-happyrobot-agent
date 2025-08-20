"""
File: negotiation_model.py
Description: SQLAlchemy model for negotiation tracking
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .call_model import CallModel
    from .carrier_model import CarrierModel
    from .load_model import LoadModel


class NegotiationModel(Base, TimestampMixin):
    """SQLAlchemy model for negotiations table."""

    __tablename__ = "negotiations"

    # Primary Key
    negotiation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Association
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.call_id"), index=True)
    load_id = Column(
        UUID(as_uuid=True), ForeignKey("loads.load_id"), nullable=False, index=True
    )
    carrier_id = Column(
        UUID(as_uuid=True), ForeignKey("carriers.carrier_id"), index=True
    )
    mc_number = Column(String(20))

    # Session Management
    session_id = Column(String(100), nullable=False, index=True)
    session_start = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    session_end = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True, index=True)

    # Negotiation Rounds
    round_number = Column(Integer, nullable=False, index=True)
    max_rounds = Column(Integer, default=3)

    # Offer Details
    carrier_offer = Column(NUMERIC(10, 2), nullable=False)
    system_response = Column(
        String(50), nullable=False
    )  # ACCEPTED, COUNTER_OFFER, REJECTED
    counter_offer = Column(NUMERIC(10, 2))

    # Context
    loadboard_rate = Column(NUMERIC(10, 2), nullable=False)
    minimum_acceptable = Column(NUMERIC(10, 2))
    maximum_acceptable = Column(NUMERIC(10, 2))

    # Decision Logic
    decision_factors = Column(JSONB)
    """
    Structure:
    {
        urgency_level, carrier_history, market_conditions,
        competitor_rates, special_requirements
    }
    """

    # Communication
    message_to_carrier = Column(Text)
    justification = Column(Text)

    # Result
    final_status = Column(
        String(30), index=True
    )  # DEAL_ACCEPTED, DEAL_REJECTED, ABANDONED, TIMEOUT
    agreed_rate = Column(NUMERIC(10, 2))

    # Timing
    response_time_seconds = Column(Integer)
    total_duration_seconds = Column(Integer)

    # Metadata
    created_by = Column(String(100))
    version = Column(Integer, default=1)

    # Relationships
    call: Mapped["CallModel"] = relationship("CallModel", foreign_keys=[call_id])
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
