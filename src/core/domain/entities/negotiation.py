"""
File: negotiation.py
Description: Negotiation domain entity
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ..value_objects import MCNumber, Rate
from ..exceptions.base import DomainException


class NegotiationLimitExceededException(DomainException):
    """Exception raised when negotiation rounds exceed limit."""
    pass


class InvalidNegotiationStateException(DomainException):
    """Exception raised when negotiation state is invalid."""
    pass


class SystemResponse(Enum):
    """System response to carrier offer."""
    ACCEPTED = "ACCEPTED"
    COUNTER_OFFER = "COUNTER_OFFER"
    REJECTED = "REJECTED"


class NegotiationStatus(Enum):
    """Final negotiation status."""
    DEAL_ACCEPTED = "DEAL_ACCEPTED"
    DEAL_REJECTED = "DEAL_REJECTED"
    ABANDONED = "ABANDONED"
    TIMEOUT = "TIMEOUT"


@dataclass
class Negotiation:
    """Domain entity for negotiations."""

    # Identity
    negotiation_id: UUID = field(default_factory=uuid4)

    # Association
    call_id: Optional[UUID] = None
    load_id: UUID = field(default=None)
    carrier_id: Optional[UUID] = None
    mc_number: Optional[MCNumber] = None

    # Session Management
    session_id: str = ""
    session_start: datetime = field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    is_active: bool = True

    # Negotiation Rounds
    round_number: int = 1
    max_rounds: int = 3

    # Offer Details
    carrier_offer: Rate = field(default=None)
    system_response: Optional[SystemResponse] = None
    counter_offer: Optional[Rate] = None

    # Context
    loadboard_rate: Rate = field(default=None)
    minimum_acceptable: Optional[Rate] = None
    maximum_acceptable: Optional[Rate] = None

    # Decision Logic
    decision_factors: Optional[Dict[str, Any]] = None

    # Communication
    message_to_carrier: Optional[str] = None
    justification: Optional[str] = None

    # Result
    final_status: Optional[NegotiationStatus] = None
    agreed_rate: Optional[Rate] = None

    # Timing
    response_time_seconds: Optional[int] = None
    total_duration_seconds: Optional[int] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1

    @property
    def offer_difference(self) -> Rate:
        """Calculate difference between carrier offer and loadboard rate."""
        return self.carrier_offer.subtract(self.loadboard_rate)

    @property
    def percentage_over(self) -> float:
        """Calculate percentage over loadboard rate."""
        return self.carrier_offer.percentage_difference(self.loadboard_rate)

    @property
    def can_continue_negotiation(self) -> bool:
        """Check if negotiation can continue (within round limits)."""
        return (
            self.is_active and
            self.round_number < self.max_rounds and
            self.final_status is None
        )

    @property
    def is_completed(self) -> bool:
        """Check if negotiation is completed."""
        return self.final_status is not None

    def evaluate_offer(self,
                      urgency_factor: float = 1.0,
                      history_factor: float = 1.0,
                      market_factor: float = 1.0) -> SystemResponse:
        """Evaluate carrier offer and determine system response."""
        if not self.is_active:
            raise InvalidNegotiationStateException("Negotiation is not active")

        if self.is_completed:
            raise InvalidNegotiationStateException("Negotiation is already completed")

        # Calculate acceptable range
        if not self.minimum_acceptable:
            self.minimum_acceptable = self.loadboard_rate.multiply(0.95)  # 5% below

        if not self.maximum_acceptable:
            self.maximum_acceptable = self.loadboard_rate.multiply(
                urgency_factor * history_factor * market_factor
            )

        # Auto-accept threshold (2% above loadboard)
        auto_accept_threshold = self.loadboard_rate.multiply(1.02)

        # Decision logic
        if self.carrier_offer <= auto_accept_threshold:
            # Accept immediately if within auto-accept threshold
            response = SystemResponse.ACCEPTED
            self.message_to_carrier = "Offer accepted. Proceeding with booking."
            self.justification = "Offer within auto-accept threshold"
        elif self.carrier_offer <= self.maximum_acceptable:
            # Accept if within maximum acceptable range
            response = SystemResponse.ACCEPTED
            self.message_to_carrier = "Offer accepted. Proceeding with booking."
            self.justification = f"Offer within acceptable range (max: {self.maximum_acceptable})"
        elif self.can_continue_negotiation:
            # Counter-offer if we can continue negotiating
            response = SystemResponse.COUNTER_OFFER
            # Calculate counter offer (between loadboard rate and carrier offer)
            counter_percentage = 0.7  # Start at 70% between rates
            difference = self.carrier_offer.subtract(self.loadboard_rate)
            counter_amount = difference.multiply(counter_percentage)
            self.counter_offer = self.loadboard_rate.add(counter_amount)

            self.message_to_carrier = f"I understand you need ${self.carrier_offer}, but the best I can do is ${self.counter_offer}."
            self.justification = "Counter-offering to find middle ground"
        else:
            # Reject if we've reached max rounds or offer is too high
            response = SystemResponse.REJECTED
            self.message_to_carrier = f"I'm sorry, but ${self.carrier_offer} is beyond our budget. Our maximum for this load is ${self.maximum_acceptable}."
            self.justification = f"Offer exceeds maximum acceptable rate or max rounds reached"

        # Record decision factors
        self.decision_factors = {
            "urgency_factor": urgency_factor,
            "history_factor": history_factor,
            "market_factor": market_factor,
            "auto_accept_threshold": auto_accept_threshold.to_float(),
            "minimum_acceptable": self.minimum_acceptable.to_float(),
            "maximum_acceptable": self.maximum_acceptable.to_float(),
            "offer_percentage_over": self.percentage_over
        }

        self.system_response = response
        self.updated_at = datetime.utcnow()

        return response

    def accept_deal(self, agreed_rate: Optional[Rate] = None) -> None:
        """Accept the deal and finalize negotiation."""
        if self.is_completed:
            raise InvalidNegotiationStateException("Negotiation is already completed")

        self.final_status = NegotiationStatus.DEAL_ACCEPTED
        self.agreed_rate = agreed_rate or self.carrier_offer
        self.session_end = datetime.utcnow()
        self.is_active = False

        # Calculate total duration
        if self.session_start:
            duration = self.session_end - self.session_start
            self.total_duration_seconds = int(duration.total_seconds())

        self.updated_at = datetime.utcnow()

    def reject_deal(self, reason: Optional[str] = None) -> None:
        """Reject the deal and finalize negotiation."""
        if self.is_completed:
            raise InvalidNegotiationStateException("Negotiation is already completed")

        self.final_status = NegotiationStatus.DEAL_REJECTED
        self.session_end = datetime.utcnow()
        self.is_active = False

        if reason:
            if self.justification:
                self.justification += f" | {reason}"
            else:
                self.justification = reason

        # Calculate total duration
        if self.session_start:
            duration = self.session_end - self.session_start
            self.total_duration_seconds = int(duration.total_seconds())

        self.updated_at = datetime.utcnow()

    def advance_round(self, new_carrier_offer: Rate) -> None:
        """Advance to the next round of negotiation."""
        if not self.can_continue_negotiation:
            raise NegotiationLimitExceededException(
                f"Cannot advance beyond round {self.max_rounds}"
            )

        self.round_number += 1
        self.carrier_offer = new_carrier_offer
        self.system_response = None
        self.counter_offer = None
        self.message_to_carrier = None
        self.justification = None
        self.updated_at = datetime.utcnow()

    def abandon_negotiation(self, reason: Optional[str] = None) -> None:
        """Abandon the negotiation (e.g., carrier hung up)."""
        self.final_status = NegotiationStatus.ABANDONED
        self.session_end = datetime.utcnow()
        self.is_active = False

        if reason:
            self.justification = f"Abandoned: {reason}"

        # Calculate total duration
        if self.session_start:
            duration = self.session_end - self.session_start
            self.total_duration_seconds = int(duration.total_seconds())

        self.updated_at = datetime.utcnow()

    def timeout_negotiation(self) -> None:
        """Mark negotiation as timed out."""
        self.final_status = NegotiationStatus.TIMEOUT
        self.session_end = datetime.utcnow()
        self.is_active = False
        self.justification = "Negotiation timed out"

        # Calculate total duration
        if self.session_start:
            duration = self.session_end - self.session_start
            self.total_duration_seconds = int(duration.total_seconds())

        self.updated_at = datetime.utcnow()

    def __eq__(self, other) -> bool:
        if isinstance(other, Negotiation):
            return self.negotiation_id == other.negotiation_id
        return False

    def __hash__(self) -> int:
        return hash(self.negotiation_id)

    def __str__(self) -> str:
        return f"Negotiation(negotiation_id={self.negotiation_id}, round={self.round_number}, response={self.system_response})"
