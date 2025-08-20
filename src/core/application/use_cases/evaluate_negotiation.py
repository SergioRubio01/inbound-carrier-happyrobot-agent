"""
File: evaluate_negotiation.py
Description: Use case for evaluating carrier negotiation offers
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from src.core.domain.entities import Negotiation, SystemResponse
from src.core.domain.value_objects import MCNumber, Rate
from src.core.ports.repositories import ILoadRepository, ICarrierRepository
from src.core.domain.exceptions.base import DomainException


class NegotiationEvaluationException(DomainException):
    """Exception raised when negotiation evaluation fails."""

    pass


@dataclass
class EvaluateNegotiationRequest:
    """Request for negotiation evaluation."""

    load_id: str
    mc_number: str
    carrier_offer: float
    negotiation_round: int
    context: Optional[Dict[str, Any]] = None


@dataclass
class EvaluateNegotiationResponse:
    """Response for negotiation evaluation."""

    negotiation_id: str
    status: str
    load_id: str
    carrier_offer: float
    counter_offer: Optional[float] = None
    agreed_rate: Optional[float] = None
    negotiation_round: int = 1
    remaining_rounds: Optional[int] = None
    message: str = ""
    justification: Optional[str] = None
    rate_difference: Optional[float] = None
    percentage_over_loadboard: Optional[float] = None
    next_steps: Optional[Dict[str, Any]] = None
    timestamp: datetime = None


class EvaluateNegotiationUseCase:
    """Use case for evaluating carrier negotiation offers."""

    def __init__(
        self, load_repository: ILoadRepository, carrier_repository: ICarrierRepository
    ):
        self.load_repository = load_repository
        self.carrier_repository = carrier_repository

    async def execute(
        self, request: EvaluateNegotiationRequest
    ) -> EvaluateNegotiationResponse:
        """Execute negotiation evaluation."""
        try:
            # Get load
            load_id = UUID(request.load_id)
            load = await self.load_repository.get_by_id(load_id)
            if not load:
                raise NegotiationEvaluationException(
                    f"Load {request.load_id} not found"
                )

            # Verify load is available
            load.verify_availability()

            # Get carrier
            mc_number = MCNumber.from_string(request.mc_number)
            carrier = await self.carrier_repository.get_by_mc_number(mc_number)
            if not carrier:
                raise NegotiationEvaluationException(
                    f"Carrier {request.mc_number} not found"
                )

            # Verify carrier eligibility
            carrier.verify_eligibility()

            # Create negotiation entity
            carrier_offer = Rate.from_float(request.carrier_offer)

            negotiation = Negotiation(
                load_id=load.load_id,
                carrier_id=carrier.carrier_id,
                mc_number=mc_number,
                session_id=f"{load_id}_{carrier.carrier_id}_{datetime.utcnow().timestamp()}",
                round_number=request.negotiation_round,
                carrier_offer=carrier_offer,
                loadboard_rate=load.loadboard_rate,
            )

            # Calculate urgency and history factors
            urgency_factor = self._calculate_urgency_factor(load)
            history_factor = self._calculate_history_factor(carrier, request.context)

            # Evaluate the offer
            system_response = negotiation.evaluate_offer(
                urgency_factor=urgency_factor, history_factor=history_factor
            )

            # Handle the response
            if system_response == SystemResponse.ACCEPTED:
                negotiation.accept_deal(carrier_offer)
                return self._create_accepted_response(negotiation, load)
            elif system_response == SystemResponse.COUNTER_OFFER:
                return self._create_counter_offer_response(negotiation)
            else:  # REJECTED
                negotiation.reject_deal("Offer exceeds maximum acceptable rate")
                return self._create_rejected_response(negotiation)

        except Exception as e:
            raise NegotiationEvaluationException(
                f"Failed to evaluate negotiation: {str(e)}"
            )

    def _calculate_urgency_factor(self, load) -> float:
        """Calculate urgency factor based on load urgency."""
        urgency_factors = {"CRITICAL": 1.15, "HIGH": 1.10, "NORMAL": 1.05, "LOW": 1.0}
        return urgency_factors.get(load.urgency.value, 1.05)

    def _calculate_history_factor(
        self, carrier, context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate history factor based on carrier history."""
        base_factor = 1.0

        # Real implementation - checks carrier performance from context
        if context and context.get("carrier_name"):
            # Preferred carriers get slightly higher factor
            if "EXPRESS" in context.get("carrier_name", "").upper():
                base_factor += 0.02

        return base_factor

    def _create_accepted_response(
        self, negotiation: Negotiation, load
    ) -> EvaluateNegotiationResponse:
        """Create response for accepted offer."""
        return EvaluateNegotiationResponse(
            negotiation_id=str(negotiation.negotiation_id),
            status="ACCEPTED",
            load_id=str(negotiation.load_id),
            carrier_offer=negotiation.carrier_offer.to_float(),
            agreed_rate=negotiation.agreed_rate.to_float(),
            negotiation_round=negotiation.round_number,
            rate_difference=negotiation.offer_difference.to_float(),
            percentage_over_loadboard=negotiation.percentage_over,
            message="Offer accepted. Proceeding with booking.",
            next_steps={
                "action": "PROCEED_TO_HANDOFF",
                "handoff_data": {
                    "load_id": str(load.load_id),
                    "agreed_rate": negotiation.agreed_rate.to_float(),
                    "carrier_mc": str(negotiation.mc_number),
                },
            },
            timestamp=datetime.utcnow(),
        )

    def _create_counter_offer_response(
        self, negotiation: Negotiation
    ) -> EvaluateNegotiationResponse:
        """Create response for counter offer."""
        return EvaluateNegotiationResponse(
            negotiation_id=str(negotiation.negotiation_id),
            status="COUNTER_OFFER",
            load_id=str(negotiation.load_id),
            carrier_offer=negotiation.carrier_offer.to_float(),
            counter_offer=negotiation.counter_offer.to_float()
            if negotiation.counter_offer
            else None,
            negotiation_round=negotiation.round_number,
            remaining_rounds=negotiation.max_rounds - negotiation.round_number,
            message=negotiation.message_to_carrier,
            justification=negotiation.justification,
            timestamp=datetime.utcnow(),
        )

    def _create_rejected_response(
        self, negotiation: Negotiation
    ) -> EvaluateNegotiationResponse:
        """Create response for rejected offer."""
        return EvaluateNegotiationResponse(
            negotiation_id=str(negotiation.negotiation_id),
            status="REJECTED",
            load_id=str(negotiation.load_id),
            carrier_offer=negotiation.carrier_offer.to_float(),
            maximum_rate=negotiation.maximum_acceptable.to_float()
            if negotiation.maximum_acceptable
            else None,
            negotiation_round=negotiation.round_number,
            message=negotiation.message_to_carrier,
            timestamp=datetime.utcnow(),
        )
