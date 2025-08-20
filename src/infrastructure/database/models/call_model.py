"""
File: call_model.py
Description: SQLAlchemy model for call tracking
Author: HappyRobot Team
Created: 2024-08-14
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, ARRAY
from sqlalchemy.orm import relationship
import uuid

from src.infrastructure.database.base import Base, TimestampMixin


class CallModel(Base, TimestampMixin):
    """SQLAlchemy model for calls table."""

    __tablename__ = "calls"

    # Primary Key
    call_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Call Identification
    external_call_id = Column(
        String(100), index=True
    )  # From HappyRobot or phone system
    session_id = Column(String(100))

    # Carrier Information
    mc_number = Column(String(20), index=True)
    carrier_id = Column(
        UUID(as_uuid=True), ForeignKey("carriers.carrier_id"), index=True
    )
    caller_phone = Column(String(20), index=True)
    caller_name = Column(String(100))

    # Load Association
    load_id = Column(UUID(as_uuid=True), ForeignKey("loads.load_id"), index=True)
    multiple_loads_discussed = Column(
        ARRAY(UUID(as_uuid=True))
    )  # Array of load IDs discussed

    # Call Metadata
    start_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_time = Column(TIMESTAMP(timezone=True), index=True)
    duration_seconds = Column(Integer)

    # Call Type and Channel
    call_type = Column(String(30), nullable=False)  # INBOUND, OUTBOUND, CALLBACK
    channel = Column(String(30))  # VOICE, WEB_CALL, API_TRIGGERED
    agent_type = Column(String(30))  # AI, HUMAN, HYBRID
    agent_id = Column(String(50))

    # Outcome Classification
    outcome = Column(String(50), nullable=False, index=True)
    # ACCEPTED, DECLINED, NEGOTIATION_FAILED, NO_EQUIPMENT,
    # CALLBACK_REQUESTED, NOT_ELIGIBLE, WRONG_LANE, INFORMATION_ONLY
    outcome_confidence = Column(NUMERIC(3, 2))  # 0.00 to 1.00

    # Sentiment Analysis
    sentiment = Column(String(20), index=True)  # POSITIVE, NEUTRAL, NEGATIVE
    sentiment_score = Column(NUMERIC(3, 2))  # -1.00 to 1.00
    sentiment_breakdown = Column(JSONB)  # {frustration: 0.2, satisfaction: 0.8}

    # Financial
    initial_offer = Column(NUMERIC(10, 2))
    final_rate = Column(NUMERIC(10, 2))
    rate_accepted = Column(Boolean)

    # Extracted Data
    extracted_data = Column(JSONB)
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
    transcript = Column(Text)
    transcript_summary = Column(Text)
    key_points = Column(ARRAY(Text))

    # Handoff Information
    transferred_to_human = Column(Boolean, default=False, index=True)
    transfer_reason = Column(String(100))
    transferred_at = Column(TIMESTAMP(timezone=True))
    assigned_rep_id = Column(String(50))

    # Follow-up
    follow_up_required = Column(Boolean, default=False, index=True)
    follow_up_reason = Column(Text)
    follow_up_deadline = Column(TIMESTAMP(timezone=True))
    follow_up_completed = Column(Boolean, default=False)

    # Recording
    recording_url = Column(Text)
    recording_duration_seconds = Column(Integer)

    # Quality
    quality_score = Column(Integer)  # 0-100
    quality_issues = Column(ARRAY(Text))

    # Metadata
    created_by = Column(String(100))
    version = Column(Integer, default=1)

    # Relationships
    carrier = relationship("CarrierModel", foreign_keys=[carrier_id])
    load = relationship("LoadModel", foreign_keys=[load_id])

    def __repr__(self) -> str:
        return f"<CallModel(call_id='{self.call_id}', mc_number='{self.mc_number}', outcome='{self.outcome}')>"
