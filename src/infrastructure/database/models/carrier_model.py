"""
File: carrier_model.py
Description: SQLAlchemy model for carrier information
Author: HappyRobot Team
Created: 2024-08-14
"""

from sqlalchemy import Column, String, Boolean, Date, Integer, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
import uuid

from src.infrastructure.database.base import Base, TimestampMixin


class CarrierModel(Base, TimestampMixin):
    """SQLAlchemy model for carriers table."""

    __tablename__ = "carriers"

    # Primary Key
    carrier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Carrier Identification
    mc_number = Column(String(20), unique=True, nullable=False, index=True)
    dot_number = Column(String(20), index=True)

    # Company Information
    legal_name = Column(String(255), nullable=False)
    dba_name = Column(String(255))

    # Status Information
    entity_type = Column(String(50), nullable=False)  # CARRIER, BROKER, BOTH
    operating_status = Column(
        String(50), nullable=False
    )  # AUTHORIZED_FOR_HIRE, NOT_AUTHORIZED, OUT_OF_SERVICE
    status = Column(String(20), nullable=False)  # ACTIVE, INACTIVE

    # Insurance Information
    insurance_on_file = Column(Boolean, default=False)
    bipd_required = Column(NUMERIC(12, 2))
    bipd_on_file = Column(NUMERIC(12, 2))
    cargo_required = Column(NUMERIC(12, 2))
    cargo_on_file = Column(NUMERIC(12, 2))
    bond_required = Column(NUMERIC(12, 2))
    bond_on_file = Column(NUMERIC(12, 2))

    # Safety Information
    safety_rating = Column(String(20))  # SATISFACTORY, CONDITIONAL, UNSATISFACTORY
    safety_rating_date = Column(Date)
    safety_scores = Column(JSONB)  # Stores BASICS scores

    # Contact Information
    primary_contact = Column(JSONB)  # {name, phone, email, title}
    address = Column(JSONB)  # {street, city, state, zip, country}

    # Eligibility (computed property in business logic)
    eligibility_notes = Column(Text)

    # Verification
    last_verified_at = Column(TIMESTAMP(timezone=True))
    verification_source = Column(String(50))  # FMCSA, MANUAL, THIRD_PARTY

    # Metadata
    created_by = Column(String(100))
    version = Column(Integer, default=1)

    @property
    def is_eligible(self) -> bool:
        """Check if carrier is eligible for business."""
        return (
            self.operating_status == "AUTHORIZED_FOR_HIRE"
            and self.status == "ACTIVE"
            and self.insurance_on_file is True
        )

    def __repr__(self) -> str:
        return f"<CarrierModel(mc_number='{self.mc_number}', legal_name='{self.legal_name}')>"
