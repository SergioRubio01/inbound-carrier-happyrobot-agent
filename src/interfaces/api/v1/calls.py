"""
File: calls.py
Description: Call management API endpoints
Author: HappyRobot Team
Created: 2024-08-14
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities import Call
from src.core.domain.entities.call import CallOutcome, CallType, Sentiment
from src.core.domain.value_objects import MCNumber, Rate
from src.infrastructure.database.postgres import (
    PostgresCallRepository,
    PostgresCarrierRepository,
    PostgresLoadRepository,
)
from src.interfaces.api.v1.dependencies.database import get_database_session

router = APIRouter(prefix="/calls", tags=["Calls"])


class HandoffRequestModel(BaseModel):
    """Request model for call handoff."""

    load_id: str
    mc_number: str
    agreed_rate: float
    carrier_contact: Dict[str, Any]
    call_summary: Optional[Dict[str, Any]] = None
    handoff_reason: str = "DEAL_ACCEPTED"
    priority: str = "NORMAL"
    preferred_rep: Optional[str] = None


class HandoffResponseModel(BaseModel):
    """Response model for call handoff."""

    handoff_id: str
    status: str
    assigned_rep: Optional[Dict[str, Any]] = None
    transfer_instructions: Optional[Dict[str, Any]] = None
    context_token: Optional[str] = None
    message: str
    timestamp: str


class FinalizeCallRequestModel(BaseModel):
    """Request model for call finalization."""

    call_id: Optional[str] = None
    mc_number: str
    load_id: Optional[str] = None
    agreed_rate: Optional[float] = None
    call_data: Dict[str, Any]
    transcript: Optional[str] = None
    extracted_data: Dict[str, Any]
    outcome: str
    sentiment: str
    follow_up_required: bool = False
    notes: Optional[str] = None


class FinalizeCallResponseModel(BaseModel):
    """Response model for call finalization."""

    call_id: str
    status: str
    data_extraction: Dict[str, Any]
    classification: Dict[str, Any]
    analytics: Optional[Dict[str, Any]] = None
    next_actions: Optional[list] = None
    message: str
    timestamp: str


@router.post("/handoff", response_model=HandoffResponseModel)
async def handoff_call(
    request: HandoffRequestModel, session: AsyncSession = Depends(get_database_session)
):
    """
    Initiate handoff to human sales representative.

    This endpoint creates a handoff request when a deal has been negotiated
    and needs to be transferred to a human sales representative.
    """
    try:
        # Initialize repositories
        load_repo = PostgresLoadRepository(session)
        carrier_repo = PostgresCarrierRepository(session)
        call_repo = PostgresCallRepository(session)

        # Validate load exists
        try:
            load_id = UUID(request.load_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid load ID format")

        load = await load_repo.get_by_id(load_id)
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")

        # Validate carrier exists
        mc_number = MCNumber.from_string(request.mc_number)
        carrier = await carrier_repo.get_by_mc_number(mc_number)
        if not carrier:
            raise HTTPException(status_code=404, detail="Carrier not found")

        # Generate handoff ID
        handoff_id = f"handoff_{datetime.utcnow().timestamp()}"

        # Create call record for handoff
        call = Call(
            mc_number=mc_number,
            carrier_id=carrier.carrier_id,
            load_id=load.load_id,
            start_time=datetime.utcnow(),
            call_type=CallType.INBOUND,
            outcome=CallOutcome.ACCEPTED,
            final_rate=Rate.from_float(request.agreed_rate),
            rate_accepted=True,
            extracted_data={
                "carrier_contact": request.carrier_contact,
                "agreed_rate": request.agreed_rate,
                "handoff_reason": request.handoff_reason,
                "priority": request.priority,
            },
            transferred_to_human=True,
            transfer_reason=request.handoff_reason,
        )

        # Save call record
        saved_call = await call_repo.create(call)

        # In a real system, this would integrate with sales rep availability system
        # For now, return a structured handoff response
        return HandoffResponseModel(
            handoff_id=handoff_id,
            status="READY_TO_TRANSFER",
            assigned_rep={
                "id": "system_assignment",
                "name": "Next Available Representative",
                "direct_line": "+1-800-HAPPYROBOT",
                "availability": "QUEUED",
            },
            transfer_instructions={
                "method": "QUEUE_TRANSFER",
                "call_id": str(saved_call.call_id),
                "priority": request.priority,
                "context_data": {
                    "load_id": request.load_id,
                    "carrier_mc": request.mc_number,
                    "agreed_rate": request.agreed_rate,
                    "carrier_contact": request.carrier_contact,
                },
            },
            context_token=str(saved_call.call_id),
            message=f"Call queued for handoff. Priority: {request.priority}. Load: {request.load_id}",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/finalize", response_model=FinalizeCallResponseModel)
async def finalize_call(
    request: FinalizeCallRequestModel,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Log call data and extract key information.

    This endpoint logs the final details of a call including outcome,
    sentiment analysis, and extracted data points.
    """
    try:
        # Initialize repositories
        call_repo = PostgresCallRepository(session)
        carrier_repo = PostgresCarrierRepository(session)

        # Get or create call record
        if request.call_id:
            try:
                call_id = UUID(request.call_id)
                call = await call_repo.get_by_id(call_id)
                if not call:
                    raise HTTPException(status_code=404, detail="Call not found")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid call ID format")
        else:
            # Create new call record
            mc_number = MCNumber.from_string(request.mc_number)
            carrier = await carrier_repo.get_by_mc_number(mc_number)

            call = Call(
                mc_number=mc_number,
                carrier_id=carrier.carrier_id if carrier else None,
                load_id=UUID(request.load_id) if request.load_id else None,
                start_time=datetime.utcnow(),
                call_type=CallType.INBOUND,
                outcome=CallOutcome(request.outcome),
                sentiment=Sentiment(request.sentiment),
                final_rate=(
                    Rate.from_float(request.agreed_rate)
                    if request.agreed_rate
                    else None
                ),
                rate_accepted=request.agreed_rate is not None,
                extracted_data=request.extracted_data,
                transcript=request.transcript,
                follow_up_required=request.follow_up_required,
            )

            call = await call_repo.create(call)

        # Update call with finalization data
        call.end_time = datetime.utcnow()
        call.outcome = CallOutcome(request.outcome)
        call.sentiment = Sentiment(request.sentiment)
        call.extracted_data = request.extracted_data
        call.transcript = request.transcript
        call.follow_up_required = request.follow_up_required

        if request.agreed_rate:
            call.final_rate = Rate.from_float(request.agreed_rate)
            call.rate_accepted = True

        # Calculate analytics based on extracted data
        extracted_fields_count = (
            len(request.extracted_data.keys()) if request.extracted_data else 0
        )
        confidence_score = min(
            0.95, extracted_fields_count * 0.08
        )  # Max 95% confidence

        call_value_score = 50  # Base score
        if request.outcome == "ACCEPTED":
            call_value_score = 95
        elif request.outcome == "NEGOTIATION_FAILED":
            call_value_score = 70
        elif request.outcome == "CALLBACK_REQUESTED":
            call_value_score = 75
        elif request.outcome == "DECLINED":
            call_value_score = 40

        conversion_probability = 0.0
        if request.outcome == "ACCEPTED":
            conversion_probability = 1.0
        elif request.outcome == "CALLBACK_REQUESTED":
            conversion_probability = 0.65
        elif request.outcome == "NEGOTIATION_FAILED":
            conversion_probability = 0.25

        # Update call record
        updated_call = await call_repo.update(call)

        # Generate next actions based on outcome
        next_actions = []
        if request.outcome == "ACCEPTED":
            next_actions = [
                {
                    "action": "SEND_RATE_CONFIRMATION",
                    "deadline": (
                        datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
                    ),
                },
                {"action": "UPDATE_LOAD_STATUS", "status": "BOOKED"},
            ]
        elif request.outcome == "CALLBACK_REQUESTED":
            next_actions = [
                {
                    "action": "SCHEDULE_CALLBACK",
                    "deadline": (
                        datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
                    ),
                }
            ]
        elif request.follow_up_required:
            next_actions = [
                {
                    "action": "FOLLOW_UP_REQUIRED",
                    "reason": request.notes or "Follow-up requested",
                }
            ]

        return FinalizeCallResponseModel(
            call_id=str(updated_call.call_id),
            status="LOGGED",
            data_extraction={
                "success": True,
                "extracted_fields": extracted_fields_count,
                "confidence_score": confidence_score,
            },
            classification={
                "outcome": request.outcome,
                "sentiment": request.sentiment,
                "confidence": 0.92,
            },
            analytics={
                "call_value_score": call_value_score,
                "conversion_probability": conversion_probability,
                "recommended_follow_up": (
                    "Send rate confirmation"
                    if request.outcome == "ACCEPTED"
                    else "Standard follow-up"
                ),
            },
            next_actions=next_actions,
            message="Call data successfully logged and processed",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
