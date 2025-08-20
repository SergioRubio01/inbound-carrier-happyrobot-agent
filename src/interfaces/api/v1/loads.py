"""
File: loads.py
Description: Load search API endpoints
Author: HappyRobot Team
Created: 2024-08-14
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.value_objects import EquipmentType, Rate
from src.core.ports.repositories import LoadSearchCriteria
from src.infrastructure.database.postgres import PostgresLoadRepository

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session

router = APIRouter(prefix="/loads", tags=["Loads"])


class LocationModel(BaseModel):
    """Location model for requests."""

    city: Optional[str] = None
    state: Optional[str] = None
    radius_miles: Optional[int] = None


class DateRangeModel(BaseModel):
    """Date range model for requests."""

    start: Optional[str] = None
    end: Optional[str] = None


class WeightRangeModel(BaseModel):
    """Weight range model for requests."""

    min: Optional[int] = None
    max: Optional[int] = None


class LoadSearchRequestModel(BaseModel):
    """Request model for load search."""

    equipment_type: str
    origin: Optional[LocationModel] = None
    destination: Optional[LocationModel] = None
    pickup_date_range: Optional[DateRangeModel] = None
    minimum_rate: Optional[float] = None
    maximum_miles: Optional[int] = None
    commodity_types: Optional[List[str]] = None
    weight_range: Optional[WeightRangeModel] = None
    limit: int = 10
    sort_by: str = "rate_per_mile_desc"


class LoadSearchResponseModel(BaseModel):
    """Response model for load search."""

    search_criteria: Dict[str, Any]
    total_matches: int
    returned_count: int
    loads: List[Dict[str, Any]]
    suggestions: Optional[Dict[str, Any]] = None
    search_timestamp: str


@router.post("/search", response_model=LoadSearchResponseModel)
async def search_loads(
    request: LoadSearchRequestModel,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Search for available loads based on criteria.

    This endpoint searches for loads that match the provided criteria including
    equipment type, origin, destination, dates, and other filters.
    """
    try:
        # Initialize repository
        load_repo = PostgresLoadRepository(session)

        # Create search criteria from request
        criteria = LoadSearchCriteria(
            equipment_type=EquipmentType.from_name(request.equipment_type),
            origin_state=request.origin.state if request.origin else None,
            destination_state=(
                request.destination.state if request.destination else None
            ),
            minimum_rate=(
                Rate.from_float(request.minimum_rate) if request.minimum_rate else None
            ),
            maximum_miles=request.maximum_miles,
            weight_min=request.weight_range.min if request.weight_range else None,
            weight_max=request.weight_range.max if request.weight_range else None,
            is_active=True,
            limit=request.limit,
            offset=0,
            sort_by=request.sort_by,
        )

        # Search loads using repository
        loads = await load_repo.search_loads(criteria)
        total_count = await load_repo.count_loads_by_criteria(criteria)

        # Convert domain entities to API response format
        load_data = []
        for load in loads:
            load_dict = {
                "load_id": str(load.load_id),
                "reference_number": load.reference_number,
                "origin": {
                    "city": load.origin.city if load.origin else None,
                    "state": load.origin.state if load.origin else None,
                    "zip": load.origin.zip_code if load.origin else None,
                },
                "destination": {
                    "city": load.destination.city if load.destination else None,
                    "state": load.destination.state if load.destination else None,
                    "zip": load.destination.zip_code if load.destination else None,
                },
                "pickup_date": (
                    load.pickup_date.isoformat() if load.pickup_date else None
                ),
                "delivery_date": (
                    load.delivery_date.isoformat() if load.delivery_date else None
                ),
                "equipment_type": (
                    load.equipment_type.name if load.equipment_type else None
                ),
                "weight": load.weight,
                "commodity": load.commodity_type,
                "distance_miles": load.miles,
                "loadboard_rate": (
                    float(load.loadboard_rate.to_float())
                    if load.loadboard_rate
                    else None
                ),
                "rate_per_mile": (
                    load.rate_per_mile.to_float() if load.rate_per_mile else None
                ),
                "broker_company": load.broker_company,
                "status": load.status.value,
                "urgency": load.urgency.value,
                "special_requirements": load.special_requirements,
                "notes": load.notes,
            }
            load_data.append(load_dict)

        # If no loads found, return empty results

        return LoadSearchResponseModel(
            search_criteria={
                "equipment_type": request.equipment_type,
                "origin_state": request.origin.state if request.origin else None,
                "destination_state": (
                    request.destination.state if request.destination else None
                ),
                "minimum_rate": request.minimum_rate,
                "maximum_miles": request.maximum_miles,
                "applied_filters": len(
                    [
                        f
                        for f in [
                            request.minimum_rate,
                            request.maximum_miles,
                            request.origin,
                            request.destination,
                        ]
                        if f is not None
                    ]
                ),
            },
            total_matches=total_count,
            returned_count=len(load_data),
            loads=load_data,
            suggestions=(
                {
                    "alternative_equipment": [
                        "53-foot van",
                        "Reefer",
                        "Flatbed",
                        "Power Only",
                        "Step Deck",
                    ],
                    "rate_analysis": "No matches found with current criteria",
                    "recommendations": "Consider expanding search radius or adjusting rate requirements",
                }
                if len(load_data) == 0
                else None
            ),
            search_timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
