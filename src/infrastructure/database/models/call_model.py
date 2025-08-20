"""
File: call_model.py
Description: SQLAlchemy model for call tracking
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .carrier_model import CarrierModel
    from .load_model import LoadModel


class CallModel(Base, TimestampMixin):
    """SQLAlchemy model for calls table."""

    __tablename__ = "calls"

    # Primary Key
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Call Identification
    external_call_id: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, nullable=True
    )  # From HappyRobot or phone system
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Carrier Information
    mc_number: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, nullable=True
    )
    carrier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carriers.carrier_id"), index=True, nullable=True
    )
    caller_phone: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, nullable=True
    )
    caller_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Load Association
    load_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loads.load_id"), index=True, nullable=True
    )
    multiple_loads_discussed: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )  # Array of load IDs discussed

    # Call Metadata
    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), index=True, nullable=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Call Type and Channel
    call_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # INBOUND, OUTBOUND, CALLBACK
    channel: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )  # VOICE, WEB_CALL, API_TRIGGERED
    agent_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )  # AI, HUMAN, HYBRID
    agent_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Outcome Classification
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # ACCEPTED, DECLINED, NEGOTIATION_FAILED, NO_EQUIPMENT,
    # CALLBACK_REQUESTED, NOT_ELIGIBLE, WRONG_LANE, INFORMATION_ONLY
    outcome_confidence: Mapped[Optional[float]] = mapped_column(
        NUMERIC(3, 2), nullable=True
    )  # 0.00 to 1.00

    # Sentiment Analysis
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, nullable=True
    )  # POSITIVE, NEUTRAL, NEGATIVE
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        NUMERIC(3, 2), nullable=True
    )  # -1.00 to 1.00
    sentiment_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {frustration: 0.2, satisfaction: 0.8}

    # Financial
    initial_offer: Mapped[Optional[float]] = mapped_column(
        NUMERIC(10, 2), nullable=True
    )
    final_rate: Mapped[Optional[float]] = mapped_column(NUMERIC(10, 2), nullable=True)
    rate_accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Extracted Data
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    """
    Structure:
    {
        carrier_info: {
            name, equipment_count, equipment_types,
            current_location, team_drivers
        },
        requirements: {
            quick_pay, fuel_advance, special_requests
        },
        availability: {
            date, location, hours_available
        },
        competitive_data: {
            dat_rate, other_quotes
        }
    }
    """

    # Conversation
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_points: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)

    # Handoff Information
    transferred_to_human: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )
    transfer_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transferred_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    assigned_rep_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Follow-up
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    follow_up_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_deadline: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    follow_up_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recording_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Quality
    quality_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0-100
    quality_issues: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), nullable=True
    )

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    carrier: Mapped["CarrierModel"] = relationship(
        "CarrierModel", foreign_keys=[carrier_id]
    )
    load: Mapped["LoadModel"] = relationship("LoadModel", foreign_keys=[load_id])

    def __repr__(self) -> str:
        return f"<CallModel(call_id='{self.call_id}', mc_number='{self.mc_number}', outcome='{self.outcome}')>"
