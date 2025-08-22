"""
File: metrics.py
Description: Simplified Metrics API endpoints for call metrics storage and retrieval
Author: HappyRobot Team
Created: 2024-08-14
Updated: 2025-01-08 - Phase 1 metrics simplification
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.postgres import (
    PostgresCallMetricsRepository,
    PostgresCarrierRepository,
    PostgresLoadRepository,
)

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class SentimentEnum(str, Enum):
    """Sentiment values for call metrics."""

    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class CallMetricsRequestModel(BaseModel):
    """Request model for creating call metrics."""

    transcript: str = Field(
        ..., min_length=1, max_length=50000, description="Full conversation transcript"
    )
    response: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Call response (Success, Rate too high, Incorrect MC, Fallback error)",
    )
    response_reason: Optional[str] = Field(
        None, max_length=2000, description="Reason for the response"
    )
    sentiment: Optional[SentimentEnum] = Field(
        None, description="Call sentiment (Positive, Neutral, Negative)"
    )
    sentiment_reason: Optional[str] = Field(
        None, max_length=2000, description="Reason for the sentiment"
    )
    session_id: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Session identifier"
    )


class CallMetricsResponseModel(BaseModel):
    """Response model for call metrics."""

    metrics_id: UUID
    transcript: str
    response: str
    response_reason: Optional[str]
    sentiment: Optional[str]
    sentiment_reason: Optional[str]
    session_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class CallMetricsCreateResponseModel(BaseModel):
    """Response model for creating call metrics."""

    metrics_id: UUID
    message: str
    created_at: datetime


class CallMetricsListResponse(BaseModel):
    """Response model for list of call metrics."""

    metrics: List[CallMetricsResponseModel]
    total_count: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]


class CallMetricsSummaryResponse(BaseModel):
    """Response model for call metrics summary statistics."""

    total_calls: int
    success_rate: float
    sentiment_distribution: Dict[str, int]
    response_distribution: Dict[str, int]
    top_response_reasons: List[Dict[str, Any]]
    top_sentiment_reasons: List[Dict[str, Any]]
    period: Dict[str, Any]


class MetricsSummaryResponseModel(BaseModel):
    """Response model for metrics summary."""

    period: Dict[str, Any]
    financial_metrics: Dict[str, Any]
    carrier_metrics: Dict[str, Any]
    generated_at: str


# New simplified call metrics endpoints
@router.post(
    "/call",
    response_model=CallMetricsCreateResponseModel,
    status_code=status.HTTP_201_CREATED,
)
async def create_call_metrics(
    request: CallMetricsRequestModel,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Store call metrics data.

    This endpoint stores essential call data including transcript, response,
    reason, and final loadboard rate for later analysis and reporting.
    """
    try:
        # Validate session_id is a valid UUID if provided
        if request.session_id:
            try:
                # Try to parse the session_id as a UUID
                uuid.UUID(request.session_id)
            except (ValueError, AttributeError, TypeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid session_id format. Must be a valid UUID string. Error: {str(e)}",
                )

        # Initialize repository
        metrics_repo = PostgresCallMetricsRepository(session)

        # Validate sentiment value if provided
        sentiment_value = None
        if request.sentiment:
            # Convert enum to string for database
            sentiment_value = (
                request.sentiment.value
                if hasattr(request.sentiment, "value")
                else str(request.sentiment)
            )

        # Create the metrics record
        metrics = await metrics_repo.create_metrics(
            transcript=request.transcript,
            response=request.response,
            response_reason=request.response_reason,
            sentiment=sentiment_value,
            sentiment_reason=request.sentiment_reason,
            session_id=request.session_id,
        )

        # Commit the transaction
        await session.commit()

        return CallMetricsCreateResponseModel(
            metrics_id=metrics.metrics_id,
            message="Metrics stored successfully",
            created_at=metrics.created_at,
        )

    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided: {str(e)}",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store metrics: {str(e)}",
        )


# Legacy summary endpoint (kept for backward compatibility)
# NOTE: This endpoint is maintained for existing integrations
@router.get("/summary", response_model=MetricsSummaryResponseModel)
async def get_metrics_summary(
    session: AsyncSession = Depends(get_database_session), days: int = 14
):
    """
    Get aggregated KPIs for dashboard display.

    DEPRECATED: This endpoint is deprecated. Use /api/v1/metrics/call endpoints instead.
    This endpoint will be removed in a future version.
    """
    try:
        # Initialize repositories
        load_repo = PostgresLoadRepository(session)
        carrier_repo = PostgresCarrierRepository(session)

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

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
            financial_metrics={
                "total_booked_revenue": load_metrics_data.get(
                    "total_booked_revenue", 0.0
                ),
                "average_load_value": load_metrics_data.get("average_load_value", 0.0),
                "average_agreed_rate": 0.0,  # Placeholder - would come from call metrics
                "average_loadboard_rate": load_metrics_data.get(
                    "average_loadboard_rate", 0.0
                ),
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
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Phase 2: GET endpoints for call metrics retrieval
@router.get("/call/summary", response_model=CallMetricsSummaryResponse)
async def get_call_metrics_summary(
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering (ISO 8601 format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for filtering (ISO 8601 format)"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> CallMetricsSummaryResponse:
    """Get aggregated statistics for call metrics."""
    try:
        # Initialize repository
        call_metrics_repo = PostgresCallMetricsRepository(session)

        # Get summary statistics
        summary_data = await call_metrics_repo.get_metrics_summary(
            start_date=start_date,
            end_date=end_date,
        )

        return CallMetricsSummaryResponse(
            total_calls=summary_data["total_calls"],
            success_rate=summary_data["success_rate"],
            sentiment_distribution=summary_data["sentiment_distribution"],
            response_distribution=summary_data["response_distribution"],
            top_response_reasons=summary_data["top_response_reasons"],
            top_sentiment_reasons=summary_data["top_sentiment_reasons"],
            period={
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/call/{metrics_id}", response_model=CallMetricsResponseModel)
async def get_call_metrics_by_id(
    metrics_id: UUID,
    session: AsyncSession = Depends(get_database_session),
) -> CallMetricsResponseModel:
    """Get specific call metrics by ID."""
    try:
        # Initialize repository
        call_metrics_repo = PostgresCallMetricsRepository(session)

        # Get metrics by ID
        metrics = await call_metrics_repo.get_by_id(metrics_id)

        if not metrics:
            raise HTTPException(status_code=404, detail="Call metrics not found")

        return CallMetricsResponseModel(
            metrics_id=metrics.metrics_id,
            transcript=str(metrics.transcript),
            response=str(metrics.response),
            response_reason=str(metrics.response_reason)
            if metrics.response_reason
            else None,
            sentiment=str(metrics.sentiment) if metrics.sentiment else None,
            sentiment_reason=str(metrics.sentiment_reason)
            if metrics.sentiment_reason
            else None,
            session_id=str(metrics.session_id) if metrics.session_id else None,
            created_at=metrics.created_at,
            updated_at=metrics.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/call", response_model=CallMetricsListResponse)
async def get_call_metrics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering (ISO 8601 format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for filtering (ISO 8601 format)"
    ),
    limit: int = Query(
        default=100,
        le=1000,
        description="Maximum number of results to return (max 1000)",
    ),
    session: AsyncSession = Depends(get_database_session),
) -> CallMetricsListResponse:
    """Retrieve call metrics with optional date filtering and pagination."""
    try:
        # Initialize repository
        call_metrics_repo = PostgresCallMetricsRepository(session)

        # Get metrics with filters
        metrics_data = await call_metrics_repo.get_metrics(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        # Convert to response models
        metrics_response = [
            CallMetricsResponseModel(
                metrics_id=metric.metrics_id,
                transcript=str(metric.transcript),
                response=str(metric.response),
                response_reason=str(metric.response_reason)
                if hasattr(metric, "response_reason") and metric.response_reason
                else None,
                sentiment=str(metric.sentiment)
                if hasattr(metric, "sentiment") and metric.sentiment
                else None,
                sentiment_reason=str(metric.sentiment_reason)
                if hasattr(metric, "sentiment_reason") and metric.sentiment_reason
                else None,
                session_id=str(metric.session_id) if metric.session_id else None,
                created_at=metric.created_at,
                updated_at=metric.updated_at,
            )
            for metric in metrics_data
        ]

        # Get total count - use count query for better performance
        total_count = await call_metrics_repo.count_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        return CallMetricsListResponse(
            metrics=metrics_response,
            total_count=total_count,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/call/{metrics_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call_metrics(
    metrics_id: UUID,
    session: AsyncSession = Depends(get_database_session),
) -> None:
    """
    Delete specific call metrics by ID.

    This endpoint permanently removes call metrics data from the system.
    The operation cannot be undone.

    Args:
        metrics_id: The unique identifier of the metrics record to delete

    Returns:
        - 204 No Content: Metrics successfully deleted
        - 404 Not Found: Metrics with given ID does not exist
        - 500 Internal Server Error: Database or system error
    """
    try:
        # Initialize repository
        call_metrics_repo = PostgresCallMetricsRepository(session)

        # Attempt to delete the metrics
        deleted = await call_metrics_repo.delete(metrics_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call metrics with ID {metrics_id} not found",
            )

        # Commit the transaction
        await session.commit()

        # Return 204 No Content on successful deletion
        return None

    except HTTPException:
        # Re-raise HTTP exceptions
        await session.rollback()
        raise
    except Exception as e:
        # Handle unexpected errors
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metrics: {str(e)}",
        )
