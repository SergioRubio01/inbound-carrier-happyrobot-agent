"""
File: negotiations.py
Description: Negotiation API endpoints
Author: HappyRobot Team
Created: 2024-08-14
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session
from src.infrastructure.database.postgres import (
    PostgresLoadRepository,
    PostgresCarrierRepository,
    PostgresNegotiationRepository,
)
from src.core.domain.value_objects import MCNumber, Rate
from src.core.domain.entities import Negotiation, SystemResponse

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])


class EvaluateNegotiationRequestModel(BaseModel):
    """Request model for negotiation evaluation."""

    load_id: str
    mc_number: str
    carrier_offer: float
    negotiation_round: int
    context: Optional[Dict[str, Any]] = None


class EvaluateNegotiationResponseModel(BaseModel):
    """Response model for negotiation evaluation."""

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
    timestamp: str


@router.post("/evaluate", response_model=EvaluateNegotiationResponseModel)
async def evaluate_negotiation(
    request: EvaluateNegotiationRequestModel,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Evaluate carrier's counter-offer for a load.

    This endpoint evaluates a carrier's offer and determines whether to accept,
    counter-offer, or reject based on business rules and negotiation state.
    """
    try:
        from datetime import datetime
        from uuid import UUID

        # Initialize repositories
        load_repo = PostgresLoadRepository(session)
        carrier_repo = PostgresCarrierRepository(session)
        negotiation_repo = PostgresNegotiationRepository(session)

        # Get load from database
        try:
            load_id = UUID(request.load_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid load ID format")

        load = await load_repo.get_by_id(load_id)
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")

        # Verify load is available
        if load.status.value != "AVAILABLE":
            raise HTTPException(
                status_code=400, detail="Load is not available for negotiation"
            )

        # Get carrier from database
        mc_number = MCNumber.from_string(request.mc_number)
        carrier = await carrier_repo.get_by_mc_number(mc_number)
        if not carrier:
            raise HTTPException(status_code=404, detail="Carrier not found")

        # Verify carrier eligibility
        if not carrier.is_eligible:
            raise HTTPException(status_code=400, detail="Carrier is not eligible")

        # Create or get existing negotiation session
        session_id = f"{load_id}_{carrier.carrier_id}_{datetime.utcnow().date()}"
        existing_negotiation = await negotiation_repo.get_by_session_id(session_id)

        if existing_negotiation and existing_negotiation.round_number >= 3:
            # Maximum rounds reached
            return EvaluateNegotiationResponseModel(
                negotiation_id=str(existing_negotiation.negotiation_id),
                status="REJECTED",
                load_id=request.load_id,
                carrier_offer=request.carrier_offer,
                counter_offer=None,
                agreed_rate=None,
                negotiation_round=request.negotiation_round,
                remaining_rounds=0,
                message="Maximum negotiation rounds reached",
                justification="Exceeded maximum allowed negotiation rounds for this load",
                rate_difference=request.carrier_offer
                - float(load.loadboard_rate.to_float()),
                percentage_over_loadboard=(
                    (request.carrier_offer - float(load.loadboard_rate.to_float()))
                    / float(load.loadboard_rate.to_float())
                )
                * 100,
                next_steps={
                    "action": "END_NEGOTIATION",
                    "reason": "Maximum rounds exceeded",
                },
                timestamp=datetime.utcnow().isoformat(),
            )

        # Create negotiation entity
        carrier_offer_rate = Rate.from_float(request.carrier_offer)

        negotiation = Negotiation(
            load_id=load.load_id,
            carrier_id=carrier.carrier_id,
            mc_number=mc_number,
            session_id=session_id,
            round_number=request.negotiation_round,
            carrier_offer=carrier_offer_rate,
            loadboard_rate=load.loadboard_rate,
        )

        # Calculate urgency factor based on load urgency
        urgency_factors = {"CRITICAL": 1.15, "HIGH": 1.10, "NORMAL": 1.05, "LOW": 1.0}
        urgency_factor = urgency_factors.get(load.urgency.value, 1.05)

        # History factor based on context
        history_factor = 1.0
        if request.context and request.context.get("carrier_performance"):
            performance = request.context["carrier_performance"]
            if performance == "excellent":
                history_factor = 1.02
            elif performance == "good":
                history_factor = 1.01

        # Evaluate the offer
        system_response = negotiation.evaluate_offer(
            urgency_factor=urgency_factor, history_factor=history_factor
        )

        # Save negotiation to database
        saved_negotiation = await negotiation_repo.create(negotiation)

        # Build response based on system decision
        rate_difference = request.carrier_offer - float(load.loadboard_rate.to_float())
        percentage_over_loadboard = (
            rate_difference / float(load.loadboard_rate.to_float())
        ) * 100

        if system_response == SystemResponse.ACCEPTED:
            negotiation.accept_deal(carrier_offer_rate)
            await negotiation_repo.update(negotiation)

            return EvaluateNegotiationResponseModel(
                negotiation_id=str(saved_negotiation.negotiation_id),
                status="ACCEPTED",
                load_id=request.load_id,
                carrier_offer=request.carrier_offer,
                counter_offer=None,
                agreed_rate=request.carrier_offer,
                negotiation_round=request.negotiation_round,
                remaining_rounds=0,
                message="Offer accepted. Proceeding with booking.",
                justification=negotiation.justification,
                rate_difference=rate_difference,
                percentage_over_loadboard=percentage_over_loadboard,
                next_steps={
                    "action": "PROCEED_TO_BOOKING",
                    "booking_required": True,
                    "handoff_data": {
                        "load_id": request.load_id,
                        "agreed_rate": request.carrier_offer,
                        "carrier_mc": request.mc_number,
                    },
                },
                timestamp=datetime.utcnow().isoformat(),
            )
        elif system_response == SystemResponse.COUNTER_OFFER:
            counter_rate = negotiation.counter_offer.to_float()
            await negotiation_repo.update(negotiation)

            return EvaluateNegotiationResponseModel(
                negotiation_id=str(saved_negotiation.negotiation_id),
                status="COUNTER_OFFERED",
                load_id=request.load_id,
                carrier_offer=request.carrier_offer,
                counter_offer=counter_rate,
                agreed_rate=None,
                negotiation_round=request.negotiation_round,
                remaining_rounds=max(0, 3 - request.negotiation_round),
                message=negotiation.message_to_carrier,
                justification=negotiation.justification,
                rate_difference=rate_difference,
                percentage_over_loadboard=percentage_over_loadboard,
                next_steps={"action": "CONTINUE_NEGOTIATION", "follow_up_time": 300},
                timestamp=datetime.utcnow().isoformat(),
            )
        else:  # REJECTED
            negotiation.reject_deal("Offer exceeds maximum acceptable rate")
            await negotiation_repo.update(negotiation)

            return EvaluateNegotiationResponseModel(
                negotiation_id=str(saved_negotiation.negotiation_id),
                status="REJECTED",
                load_id=request.load_id,
                carrier_offer=request.carrier_offer,
                counter_offer=None,
                agreed_rate=None,
                negotiation_round=request.negotiation_round,
                remaining_rounds=0,
                message=negotiation.message_to_carrier,
                justification=negotiation.justification,
                rate_difference=rate_difference,
                percentage_over_loadboard=percentage_over_loadboard,
                next_steps={"action": "END_NEGOTIATION", "reason": "Offer too high"},
                timestamp=datetime.utcnow().isoformat(),
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
