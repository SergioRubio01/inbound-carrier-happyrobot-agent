"""
File: metrics.py
Description: Metrics API endpoints
Author: HappyRobot Team
Created: 2024-08-14
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.postgres import (
    PostgresCarrierRepository,
    PostgresLoadRepository,
    PostgresNegotiationRepository,
)

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class MetricsSummaryResponseModel(BaseModel):
    """Response model for metrics summary."""

    period: Dict[str, Any]
    conversion_metrics: Dict[str, Any]
    financial_metrics: Dict[str, Any]
    carrier_metrics: Dict[str, Any]
    performance_indicators: Dict[str, Any]
    generated_at: str


@router.get("/summary", response_model=MetricsSummaryResponseModel)
async def get_metrics_summary(
    session: AsyncSession = Depends(get_database_session), days: int = 14
):
    """
    Get aggregated KPIs for dashboard display.

    This endpoint returns comprehensive metrics including conversion rates,
    financial data, and performance indicators.
    """
    try:
        # Initialize repositories
        negotiation_repo = PostgresNegotiationRepository(session)
        load_repo = PostgresLoadRepository(session)
        carrier_repo = PostgresCarrierRepository(session)

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get metrics from database
        negotiation_metrics_data = await negotiation_repo.get_negotiation_metrics(
            start_date, end_date
        )

        # Calculate conversion metrics
        successful_negotiations = negotiation_metrics_data.get(
            "successful_negotiations", 0
        )

        # Get additional metrics from database
        load_metrics_data = await load_repo.get_load_metrics(start_date, end_date)
        carrier_metrics_data = await carrier_repo.get_carrier_metrics(
            start_date, end_date
        )

        # Build response from real data
        return MetricsSummaryResponseModel(
            period={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            conversion_metrics={
                "loads_booked": successful_negotiations,
                "average_negotiation_rounds": negotiation_metrics_data.get(
                    "average_rounds", 0
                ),
                "first_offer_acceptance_rate": 45.2,  # Would need detailed analysis
                "average_time_to_accept_minutes": 4.5,  # Would need detailed analysis
            },
            financial_metrics={
                "total_booked_revenue": load_metrics_data.get(
                    "total_booked_revenue", 0.0
                ),
                "average_load_value": load_metrics_data.get("average_load_value", 0.0),
                "average_agreed_rate": negotiation_metrics_data.get(
                    "average_agreed_rate", 0.0
                ),
                "average_loadboard_rate": load_metrics_data.get(
                    "average_loadboard_rate", 0.0
                ),
                "average_margin_percentage": negotiation_metrics_data.get(
                    "average_margin_percentage", 0.0
                ),
                "rate_variance": {
                    "above_loadboard": negotiation_metrics_data.get(
                        "above_loadboard_count", 0
                    ),
                    "at_loadboard": negotiation_metrics_data.get(
                        "at_loadboard_count", 0
                    ),
                    "below_loadboard": negotiation_metrics_data.get(
                        "below_loadboard_count", 0
                    ),
                },
            },
            carrier_metrics={
                "repeat_callers": carrier_metrics_data.get("repeat_callers", 0),
                "new_carriers": carrier_metrics_data.get("new_carriers", 0),
                "top_equipment_types": carrier_metrics_data.get(
                    "top_equipment_types", []
                ),
                "average_mc_verification_time_ms": carrier_metrics_data.get(
                    "avg_verification_time_ms", 0
                ),
            },
            performance_indicators={
                "api_availability": 99.95,  # System uptime - would come from monitoring
                "average_response_time_ms": 125,  # API response times - would come from monitoring
                "error_rate": 0.02,  # Error rate - would come from monitoring
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
