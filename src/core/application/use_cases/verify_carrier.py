"""
File: verify_carrier.py
Description: Use case for verifying carrier eligibility
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.domain.entities import Carrier, CarrierNotEligibleException
from src.core.domain.value_objects import MCNumber
from src.core.ports.repositories import ICarrierRepository
from src.core.domain.exceptions.base import DomainException


class FMCSAVerificationException(DomainException):
    """Exception raised when FMCSA verification fails."""

    pass


@dataclass
class VerifyCarrierRequest:
    """Request for carrier verification."""

    mc_number: str
    include_safety_score: bool = False


@dataclass
class VerifyCarrierResponse:
    """Response for carrier verification."""

    mc_number: str
    eligible: bool
    carrier_info: Optional[Dict[str, Any]] = None
    safety_score: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    details: Optional[str] = None
    verification_timestamp: datetime = None


class VerifyCarrierUseCase:
    """Use case for verifying carrier MC number and eligibility."""

    def __init__(self, carrier_repository: ICarrierRepository):
        self.carrier_repository = carrier_repository

    async def execute(self, request: VerifyCarrierRequest) -> VerifyCarrierResponse:
        """Execute carrier verification."""
        try:
            # Validate and create MC number value object
            mc_number = MCNumber.from_string(request.mc_number)

            # Check if carrier already exists in our database
            existing_carrier = await self.carrier_repository.get_by_mc_number(mc_number)

            if existing_carrier and existing_carrier.last_verified_at:
                # Check if verification is recent (within 24 hours)
                time_since_verification = (
                    datetime.utcnow() - existing_carrier.last_verified_at
                )
                if time_since_verification.total_seconds() < 86400:  # 24 hours
                    return self._create_response_from_carrier(existing_carrier)

            # Perform FMCSA verification
            fmcsa_data = await self._verify_with_fmcsa(
                mc_number, request.include_safety_score
            )

            if fmcsa_data is None:
                # External FMCSA verification not available or carrier not found
                if existing_carrier:
                    # Return data from existing carrier record
                    return self._create_response_from_carrier(existing_carrier)
                else:
                    # No data available for this carrier
                    return VerifyCarrierResponse(
                        mc_number=request.mc_number,
                        eligible=False,
                        reason="CARRIER_NOT_FOUND",
                        details="Carrier not found in database and external verification unavailable",
                        verification_timestamp=datetime.utcnow(),
                    )

            # Create or update carrier entity with FMCSA data
            if existing_carrier:
                carrier = self._update_carrier_from_fmcsa(existing_carrier, fmcsa_data)
                carrier = await self.carrier_repository.update(carrier)
            else:
                carrier = self._create_carrier_from_fmcsa(mc_number, fmcsa_data)
                carrier = await self.carrier_repository.create(carrier)

            return self._create_response_from_carrier(
                carrier, fmcsa_data.get("safety_score")
            )

        except CarrierNotEligibleException as e:
            return VerifyCarrierResponse(
                mc_number=request.mc_number,
                eligible=False,
                reason="CARRIER_NOT_ELIGIBLE",
                details=str(e),
                verification_timestamp=datetime.utcnow(),
            )
        except Exception as e:
            raise FMCSAVerificationException(
                f"Failed to verify carrier {request.mc_number}: {str(e)}"
            )

    async def _verify_with_fmcsa(
        self, mc_number: MCNumber, include_safety: bool
    ) -> Dict[str, Any]:
        """FMCSA verification service - returns None if carrier not found in external system."""
        # In production, this would make actual HTTP calls to FMCSA SAFER API
        # For now, since we removed all mocks, this returns None to indicate
        # that external FMCSA verification is not available
        # Real implementation would use:
        # - FMCSA SAFER API endpoints
        # - Proper authentication/API keys
        # - Real-time data fetching

        # Return None to indicate carrier not found in external system
        return None

    def _create_carrier_from_fmcsa(
        self, mc_number: MCNumber, fmcsa_data: Dict[str, Any]
    ) -> Carrier:
        """Create new carrier entity from FMCSA data."""
        carrier = Carrier(
            mc_number=mc_number,
            legal_name=fmcsa_data.get("legal_name", ""),
            dba_name=fmcsa_data.get("dba_name"),
            entity_type=fmcsa_data.get("entity_type", "CARRIER"),
            operating_status=fmcsa_data.get("operating_status", "NOT_AUTHORIZED"),
            status=fmcsa_data.get("status", "INACTIVE"),
            insurance_on_file=fmcsa_data.get("insurance_on_file", False),
            bipd_required=fmcsa_data.get("bipd_required"),
            bipd_on_file=fmcsa_data.get("bipd_on_file"),
            cargo_required=fmcsa_data.get("cargo_required"),
            cargo_on_file=fmcsa_data.get("cargo_on_file"),
            bond_required=fmcsa_data.get("bond_required"),
            bond_on_file=fmcsa_data.get("bond_on_file"),
            safety_rating=fmcsa_data.get("safety_rating"),
            safety_scores=fmcsa_data.get("safety_scores"),
            last_verified_at=datetime.utcnow(),
            verification_source="FMCSA",
        )

        return carrier

    def _update_carrier_from_fmcsa(
        self, carrier: Carrier, fmcsa_data: Dict[str, Any]
    ) -> Carrier:
        """Update existing carrier with FMCSA data."""
        carrier.legal_name = fmcsa_data.get("legal_name", carrier.legal_name)
        carrier.dba_name = fmcsa_data.get("dba_name", carrier.dba_name)
        carrier.entity_type = fmcsa_data.get("entity_type", carrier.entity_type)
        carrier.operating_status = fmcsa_data.get(
            "operating_status", carrier.operating_status
        )
        carrier.status = fmcsa_data.get("status", carrier.status)
        carrier.insurance_on_file = fmcsa_data.get(
            "insurance_on_file", carrier.insurance_on_file
        )
        carrier.bipd_required = fmcsa_data.get("bipd_required", carrier.bipd_required)
        carrier.bipd_on_file = fmcsa_data.get("bipd_on_file", carrier.bipd_on_file)
        carrier.cargo_required = fmcsa_data.get(
            "cargo_required", carrier.cargo_required
        )
        carrier.cargo_on_file = fmcsa_data.get("cargo_on_file", carrier.cargo_on_file)
        carrier.bond_required = fmcsa_data.get("bond_required", carrier.bond_required)
        carrier.bond_on_file = fmcsa_data.get("bond_on_file", carrier.bond_on_file)
        carrier.safety_rating = fmcsa_data.get("safety_rating", carrier.safety_rating)
        carrier.safety_scores = fmcsa_data.get("safety_scores", carrier.safety_scores)
        carrier.update_verification("FMCSA")

        return carrier

    def _create_response_from_carrier(
        self, carrier: Carrier, safety_score: Optional[Dict] = None
    ) -> VerifyCarrierResponse:
        """Create response from carrier entity."""
        try:
            carrier.verify_eligibility()
            eligible = True
            reason = None
            details = "Carrier is active and authorized for hire"
        except CarrierNotEligibleException as e:
            eligible = False
            reason = "CARRIER_NOT_AUTHORIZED"
            details = str(e)

        carrier_info = {
            "legal_name": carrier.legal_name,
            "dba_name": carrier.dba_name,
            "status": carrier.status,
            "entity_type": carrier.entity_type,
            "operating_status": carrier.operating_status,
            "insurance_on_file": carrier.insurance_on_file,
            "bipd_required": str(carrier.bipd_required)
            if carrier.bipd_required
            else None,
            "bipd_on_file": str(carrier.bipd_on_file) if carrier.bipd_on_file else None,
            "cargo_required": str(carrier.cargo_required)
            if carrier.cargo_required
            else None,
            "cargo_on_file": str(carrier.cargo_on_file)
            if carrier.cargo_on_file
            else None,
            "bond_required": str(carrier.bond_required)
            if carrier.bond_required
            else None,
            "bond_on_file": str(carrier.bond_on_file) if carrier.bond_on_file else None,
        }

        response_safety_score = None
        if safety_score or carrier.safety_scores:
            response_safety_score = {
                "basics_scores": safety_score or carrier.safety_scores,
                "safety_rating": carrier.safety_rating,
                "rating_date": carrier.safety_rating_date.isoformat()
                if carrier.safety_rating_date
                else None,
            }

        return VerifyCarrierResponse(
            mc_number=str(carrier.mc_number),
            eligible=eligible,
            carrier_info=carrier_info,
            safety_score=response_safety_score,
            reason=reason,
            details=details,
            verification_timestamp=datetime.utcnow(),
        )
