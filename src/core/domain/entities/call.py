"""
File: call.py
Description: Call domain entity
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ..value_objects import MCNumber, Rate
from ..exceptions.base import DomainException


class InvalidCallStateException(DomainException):
    """Exception raised when call state is invalid."""

    pass


class CallType(Enum):
    """Call type enumeration."""

    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    CALLBACK = "CALLBACK"


class CallChannel(Enum):
    """Call channel enumeration."""

    VOICE = "VOICE"
    WEB_CALL = "WEB_CALL"
    API_TRIGGERED = "API_TRIGGERED"


class AgentType(Enum):
    """Agent type enumeration."""

    AI = "AI"
    HUMAN = "HUMAN"
    HYBRID = "HYBRID"


class CallOutcome(Enum):
    """Call outcome enumeration."""

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED"
    NO_EQUIPMENT = "NO_EQUIPMENT"
    CALLBACK_REQUESTED = "CALLBACK_REQUESTED"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    WRONG_LANE = "WRONG_LANE"
    INFORMATION_ONLY = "INFORMATION_ONLY"


class Sentiment(Enum):
    """Sentiment enumeration."""

    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


@dataclass
class Call:
    """Domain entity for calls."""

    # Identity
    call_id: UUID = field(default_factory=uuid4)
    external_call_id: Optional[str] = None
    session_id: Optional[str] = None

    # Carrier Information
    mc_number: Optional[MCNumber] = None
    carrier_id: Optional[UUID] = None
    caller_phone: Optional[str] = None
    caller_name: Optional[str] = None

    # Load Association
    load_id: Optional[UUID] = None
    multiple_loads_discussed: Optional[List[UUID]] = None

    # Call Metadata
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    # Call Type and Channel
    call_type: CallType = CallType.INBOUND
    channel: Optional[CallChannel] = None
    agent_type: AgentType = AgentType.AI
    agent_id: Optional[str] = None

    # Outcome Classification
    outcome: Optional[CallOutcome] = None
    outcome_confidence: Optional[float] = None  # 0.00 to 1.00

    # Sentiment Analysis
    sentiment: Optional[Sentiment] = None
    sentiment_score: Optional[float] = None  # -1.00 to 1.00
    sentiment_breakdown: Optional[Dict[str, float]] = None

    # Financial
    initial_offer: Optional[Rate] = None
    final_rate: Optional[Rate] = None
    rate_accepted: Optional[bool] = None

    # Extracted Data
    extracted_data: Optional[Dict[str, Any]] = None

    # Conversation
    transcript: Optional[str] = None
    transcript_summary: Optional[str] = None
    key_points: Optional[List[str]] = None

    # Handoff Information
    transferred_to_human: bool = False
    transfer_reason: Optional[str] = None
    transferred_at: Optional[datetime] = None
    assigned_rep_id: Optional[str] = None

    # Follow-up
    follow_up_required: bool = False
    follow_up_reason: Optional[str] = None
    follow_up_deadline: Optional[datetime] = None
    follow_up_completed: bool = False

    # Recording
    recording_url: Optional[str] = None
    recording_duration_seconds: Optional[int] = None

    # Quality
    quality_score: Optional[int] = None  # 0-100
    quality_issues: Optional[List[str]] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1

    @property
    def is_active(self) -> bool:
        """Check if call is currently active."""
        return self.end_time is None

    @property
    def was_successful(self) -> bool:
        """Check if call was successful (deal accepted)."""
        return self.outcome == CallOutcome.ACCEPTED

    @property
    def needs_follow_up(self) -> bool:
        """Check if call needs follow-up."""
        return self.follow_up_required and not self.follow_up_completed

    def end_call(
        self, outcome: CallOutcome, end_time: Optional[datetime] = None
    ) -> None:
        """End the call with an outcome."""
        if not self.is_active:
            raise InvalidCallStateException("Call is already ended")

        self.end_time = end_time or datetime.utcnow()
        self.outcome = outcome

        # Calculate duration if we have start time
        if self.start_time:
            duration = self.end_time - self.start_time
            self.duration_seconds = int(duration.total_seconds())

        self.updated_at = datetime.utcnow()

    def transfer_to_human(self, rep_id: str, reason: Optional[str] = None) -> None:
        """Transfer call to human representative."""
        if not self.is_active:
            raise InvalidCallStateException("Cannot transfer an ended call")

        self.transferred_to_human = True
        self.transfer_reason = reason
        self.transferred_at = datetime.utcnow()
        self.assigned_rep_id = rep_id
        self.agent_type = AgentType.HYBRID
        self.updated_at = datetime.utcnow()

    def add_extracted_data(self, data: Dict[str, Any]) -> None:
        """Add or update extracted data."""
        if self.extracted_data is None:
            self.extracted_data = {}

        self.extracted_data.update(data)
        self.updated_at = datetime.utcnow()

    def set_sentiment(
        self,
        sentiment: Sentiment,
        score: Optional[float] = None,
        breakdown: Optional[Dict[str, float]] = None,
    ) -> None:
        """Set sentiment analysis results."""
        self.sentiment = sentiment
        self.sentiment_score = score
        self.sentiment_breakdown = breakdown
        self.updated_at = datetime.utcnow()

    def set_financial_info(
        self,
        initial_offer: Optional[Rate] = None,
        final_rate: Optional[Rate] = None,
        accepted: Optional[bool] = None,
    ) -> None:
        """Set financial information."""
        if initial_offer:
            self.initial_offer = initial_offer
        if final_rate:
            self.final_rate = final_rate
        if accepted is not None:
            self.rate_accepted = accepted

        self.updated_at = datetime.utcnow()

    def schedule_follow_up(self, reason: str, deadline: datetime) -> None:
        """Schedule a follow-up for this call."""
        self.follow_up_required = True
        self.follow_up_reason = reason
        self.follow_up_deadline = deadline
        self.follow_up_completed = False
        self.updated_at = datetime.utcnow()

    def complete_follow_up(self) -> None:
        """Mark follow-up as completed."""
        self.follow_up_completed = True
        self.updated_at = datetime.utcnow()

    def add_quality_issue(self, issue: str) -> None:
        """Add a quality issue to the call."""
        if self.quality_issues is None:
            self.quality_issues = []

        self.quality_issues.append(issue)
        self.updated_at = datetime.utcnow()

    def __eq__(self, other) -> bool:
        if isinstance(other, Call):
            return self.call_id == other.call_id
        return False

    def __hash__(self) -> int:
        return hash(self.call_id)

    def __str__(self) -> str:
        return f"Call(call_id={self.call_id}, mc_number={self.mc_number}, outcome={self.outcome})"
