"""
File: simple_negotiations.py
Description: Simple stateless negotiation calculation endpoint
Author: HappyRobot Team
Created: 2024-08-21
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])


class NegotiationResponse(BaseModel):
    """Response model for simple negotiation calculation."""

    new_offer: float
    attempt_number: int
    message: str


@router.get("", response_model=NegotiationResponse)
async def calculate_negotiation(
    initial_offer: float = Query(..., description="Initial loadboard rate"),
    customer_offer: float = Query(..., description="Customer's current offer"),
    attempt_number: int = Query(
        ..., ge=1, le=3, description="Current negotiation attempt (1-3)"
    ),
) -> NegotiationResponse:
    """
    Calculate a simple counter-offer for negotiation.

    This endpoint provides a stateless calculation for price negotiation,
    moving 1/3 of the way from the initial offer toward the customer's offer.
    """
    # Simple negotiation formula: move 1/3 toward customer offer
    new_offer = initial_offer + (customer_offer - initial_offer) / 3

    # Round to 2 decimal places for currency
    new_offer = round(new_offer, 2)

    # Increment attempt number for next round
    next_attempt = min(attempt_number + 1, 3)

    # Generate appropriate message based on attempt
    if attempt_number >= 3:
        message = "Final offer - no further negotiation available"
    else:
        message = f"Counter-offer for round {attempt_number}"

    return NegotiationResponse(
        new_offer=new_offer, attempt_number=next_attempt, message=message
    )
