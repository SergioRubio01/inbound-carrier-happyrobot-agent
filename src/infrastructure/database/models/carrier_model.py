"""
File: carrier_model.py
Description: SQLAlchemy model for carrier information
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base, TimestampMixin


class CarrierModel(Base, TimestampMixin):
    """SQLAlchemy model for carriers table."""

    __tablename__ = "carriers"

    # Primary Key
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Carrier Identification
    mc_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    dot_number: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, nullable=True
    )

    # Company Information
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dba_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status Information
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CARRIER, BROKER, BOTH
    operating_status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # AUTHORIZED_FOR_HIRE, NOT_AUTHORIZED, OUT_OF_SERVICE
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # ACTIVE, INACTIVE

    # Insurance Information
    insurance_on_file: Mapped[bool] = mapped_column(Boolean, default=False)
    bipd_required: Mapped[Optional[float]] = mapped_column(
        NUMERIC(12, 2), nullable=True
    )
    bipd_on_file: Mapped[Optional[float]] = mapped_column(NUMERIC(12, 2), nullable=True)
    cargo_required: Mapped[Optional[float]] = mapped_column(
        NUMERIC(12, 2), nullable=True
    )
    cargo_on_file: Mapped[Optional[float]] = mapped_column(
        NUMERIC(12, 2), nullable=True
    )
    bond_required: Mapped[Optional[float]] = mapped_column(
        NUMERIC(12, 2), nullable=True
    )
    bond_on_file: Mapped[Optional[float]] = mapped_column(NUMERIC(12, 2), nullable=True)

    # Safety Information
    safety_rating: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # SATISFACTORY, CONDITIONAL, UNSATISFACTORY
    safety_rating_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    safety_scores: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Stores BASICS scores

    # Contact Information
    primary_contact: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {name, phone, email, title}
    address: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {street, city, state, zip, country}

    # Eligibility (computed property in business logic)
    eligibility_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Verification
    last_verified_at = Column(TIMESTAMP(timezone=True))
    verification_source = Column(String(50))  # EXTERNAL_API, MANUAL, THIRD_PARTY

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

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
