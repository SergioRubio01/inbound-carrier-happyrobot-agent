"""
File: carrier.py
Description: Carrier domain entity
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..value_objects import MCNumber, Location
from ..exceptions.base import DomainException


class CarrierNotEligibleException(DomainException):
    """Exception raised when carrier is not eligible for business."""
    pass


@dataclass
class Carrier:
    """Domain entity for carriers."""

    # Identity
    carrier_id: UUID = field(default_factory=uuid4)
    mc_number: MCNumber = field(default=None)
    dot_number: Optional[str] = None

    # Company Information
    legal_name: str = ""
    dba_name: Optional[str] = None

    # Status Information
    entity_type: str = ""  # CARRIER, BROKER, BOTH
    operating_status: str = ""  # AUTHORIZED_FOR_HIRE, NOT_AUTHORIZED, OUT_OF_SERVICE
    status: str = ""  # ACTIVE, INACTIVE

    # Insurance Information
    insurance_on_file: bool = False
    bipd_required: Optional[float] = None
    bipd_on_file: Optional[float] = None
    cargo_required: Optional[float] = None
    cargo_on_file: Optional[float] = None
    bond_required: Optional[float] = None
    bond_on_file: Optional[float] = None

    # Safety Information
    safety_rating: Optional[str] = None  # SATISFACTORY, CONDITIONAL, UNSATISFACTORY
    safety_rating_date: Optional[datetime] = None
    safety_scores: Optional[Dict[str, Any]] = None

    # Contact Information
    primary_contact: Optional[Dict[str, Any]] = None
    address: Optional[Location] = None

    # Eligibility
    eligibility_notes: Optional[str] = None

    # Verification
    last_verified_at: Optional[datetime] = None
    verification_source: Optional[str] = None  # EXTERNAL_API, MANUAL, THIRD_PARTY

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1

    @property
    def is_eligible(self) -> bool:
        """Check if carrier is eligible for business."""
        return (
            self.operating_status == 'AUTHORIZED_FOR_HIRE' and
            self.status == 'ACTIVE' and
            self.insurance_on_file is True
        )

    def verify_eligibility(self) -> None:
        """Verify carrier eligibility and raise exception if not eligible."""
        if not self.is_eligible:
            reasons = []

            if self.operating_status != 'AUTHORIZED_FOR_HIRE':
                reasons.append(f"Operating status: {self.operating_status}")

            if self.status != 'ACTIVE':
                reasons.append(f"Status: {self.status}")

            if not self.insurance_on_file:
                reasons.append("Insurance not on file")

            raise CarrierNotEligibleException(
                f"Carrier {self.mc_number} is not eligible: {', '.join(reasons)}"
            )

    def update_verification(self, source: str, verified_at: Optional[datetime] = None) -> None:
        """Update verification information."""
        self.verification_source = source
        self.last_verified_at = verified_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_safety_info(self, rating: str, rating_date: datetime, scores: Optional[Dict[str, Any]] = None) -> None:
        """Update safety information."""
        self.safety_rating = rating
        self.safety_rating_date = rating_date
        self.safety_scores = scores
        self.updated_at = datetime.utcnow()

    def add_eligibility_note(self, note: str) -> None:
        """Add or update eligibility notes."""
        if self.eligibility_notes:
            self.eligibility_notes += f" | {note}"
        else:
            self.eligibility_notes = note
        self.updated_at = datetime.utcnow()

    def __eq__(self, other) -> bool:
        if isinstance(other, Carrier):
            return self.carrier_id == other.carrier_id
        return False

    def __hash__(self) -> int:
        return hash(self.carrier_id)

    def __str__(self) -> str:
        return f"Carrier(mc_number={self.mc_number}, legal_name='{self.legal_name}')"
