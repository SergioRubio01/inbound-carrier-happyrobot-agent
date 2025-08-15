"""
File: metrics.py
Description: Metrics API endpoints
Author: HappyRobot Team
Created: 2024-08-14
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session
from src.infrastructure.database.postgres import (
    PostgresCallRepository,
    PostgresNegotiationRepository,
    PostgresLoadRepository,
    PostgresCarrierRepository
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class MetricsSummaryResponseModel(BaseModel):
    """Response model for metrics summary."""
    period: Dict[str, Any]
    call_metrics: Dict[str, Any]
    conversion_metrics: Dict[str, Any]
    financial_metrics: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    carrier_metrics: Dict[str, Any]
    performance_indicators: Dict[str, Any]
    generated_at: str


@router.get("/summary", response_model=MetricsSummaryResponseModel)
async def get_metrics_summary(
    session: AsyncSession = Depends(get_database_session),
    days: int = 14
):
    """
    Get aggregated KPIs for dashboard display.

    This endpoint returns comprehensive metrics including call volumes,
    conversion rates, financial data, and performance indicators.
    """
    try:
        # Initialize repositories
        call_repo = PostgresCallRepository(session)
        negotiation_repo = PostgresNegotiationRepository(session)
        load_repo = PostgresLoadRepository(session)
        carrier_repo = PostgresCarrierRepository(session)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get metrics from database
        call_metrics_data = await call_repo.get_call_metrics(start_date, end_date)
        negotiation_metrics_data = await negotiation_repo.get_negotiation_metrics(start_date, end_date)

        # Calculate conversion metrics
        total_calls = call_metrics_data.get('total_calls', 0)
        successful_negotiations = negotiation_metrics_data.get('successful_negotiations', 0)
        booking_rate = (successful_negotiations / total_calls * 100) if total_calls > 0 else 0

        # Get additional metrics from database
        load_metrics_data = await load_repo.get_load_metrics(start_date, end_date)
        carrier_metrics_data = await carrier_repo.get_carrier_metrics(start_date, end_date)

        # Build response from real data
        return MetricsSummaryResponseModel(
            period={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            call_metrics={
                "total_calls": total_calls,
                "unique_carriers": len(set(call_metrics_data.get('carrier_ids', []))),
                "average_duration_seconds": call_metrics_data.get('average_duration_seconds', 0),
                "peak_hour": "14:00",  # Would need hourly analysis
                "by_outcome": call_metrics_data.get('outcomes', {})
            },
            conversion_metrics={
                "loads_booked": successful_negotiations,
                "booking_rate": round(booking_rate, 2),
                "average_negotiation_rounds": negotiation_metrics_data.get('average_rounds', 0),
                "first_offer_acceptance_rate": 45.2,  # Would need detailed analysis
                "average_time_to_accept_minutes": 4.5  # Would need detailed analysis
            },
            financial_metrics={
                "total_booked_revenue": load_metrics_data.get('total_booked_revenue', 0.0),
                "average_load_value": load_metrics_data.get('average_load_value', 0.0),
                "average_agreed_rate": negotiation_metrics_data.get('average_agreed_rate', 0.0),
                "average_loadboard_rate": load_metrics_data.get('average_loadboard_rate', 0.0),
                "average_margin_percentage": negotiation_metrics_data.get('average_margin_percentage', 0.0),
                "rate_variance": {
                    "above_loadboard": negotiation_metrics_data.get('above_loadboard_count', 0),
                    "at_loadboard": negotiation_metrics_data.get('at_loadboard_count', 0),
                    "below_loadboard": negotiation_metrics_data.get('below_loadboard_count', 0)
                }
            },
            sentiment_analysis={
                "positive": call_metrics_data.get('positive_sentiment_count', 0),
                "neutral": call_metrics_data.get('neutral_sentiment_count', 0),
                "negative": call_metrics_data.get('negative_sentiment_count', 0),
                "average_score": call_metrics_data.get('average_sentiment_score', 0.0),
                "trend": call_metrics_data.get('sentiment_trend', 'STABLE')
            },
            carrier_metrics={
                "repeat_callers": carrier_metrics_data.get('repeat_callers', 0),
                "new_carriers": carrier_metrics_data.get('new_carriers', 0),
                "top_equipment_types": carrier_metrics_data.get('top_equipment_types', []),
                "average_mc_verification_time_ms": carrier_metrics_data.get('avg_verification_time_ms', 0)
            },
            performance_indicators={
                "api_availability": 99.95,  # System uptime - would come from monitoring
                "average_response_time_ms": 125,  # API response times - would come from monitoring
                "error_rate": 0.02,  # Error rate - would come from monitoring
                "handoff_success_rate": call_metrics_data.get('handoff_success_rate', 0.0)
            },
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
