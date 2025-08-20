"""
File: loads.py
Description: Load management API endpoints
Author: HappyRobot Team
Created: 2024-08-14
Updated: 2024-08-20
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

# Configuration
from src.config.settings import settings

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session
from src.infrastructure.database.postgres import PostgresLoadRepository

# Use cases
from src.core.application.use_cases.create_load_use_case import CreateLoadUseCase
from src.core.application.use_cases.list_loads_use_case import ListLoadsUseCase

# Domain objects
from src.core.domain.value_objects import Location

router = APIRouter(prefix="/loads", tags=["Loads"])


class LocationRequestModel(BaseModel):
    """Location model for requests."""
    city: str = Field(..., description="City name", min_length=1)
    state: str = Field(..., description="2-letter state code", min_length=2, max_length=2)
    zip: Optional[str] = Field(None, description="ZIP code")


class CreateLoadRequestModel(BaseModel):
    """Request model for creating a new load."""
    origin: LocationRequestModel = Field(..., description="Load origin location")
    destination: LocationRequestModel = Field(..., description="Load destination location")
    pickup_datetime: datetime = Field(..., description="Pickup date and time")
    delivery_datetime: datetime = Field(..., description="Delivery date and time")
    equipment_type: str = Field(..., description="Required equipment type")
    loadboard_rate: float = Field(..., gt=0, description="Loadboard rate in USD")
    weight: int = Field(..., gt=0, le=settings.max_load_weight_lbs, description="Weight in pounds")
    commodity_type: str = Field(..., description="Type of commodity")
    notes: Optional[str] = Field(None, description="Additional notes")
    reference_number: Optional[str] = Field(None, description="Custom reference number")
    broker_company: Optional[str] = Field(None, description="Broker company name")
    special_requirements: Optional[List[str]] = Field(None, description="Special requirements")
    customer_name: Optional[str] = Field(None, description="Customer name")
    dimensions: Optional[str] = Field(None, description="Load dimensions")
    pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    hazmat: bool = Field(False, description="Whether load is hazmat")
    hazmat_class: Optional[str] = Field(None, description="Hazmat class if applicable")
    miles: Optional[int] = Field(None, gt=0, description="Estimated miles")
    fuel_surcharge: Optional[float] = Field(None, ge=0, description="Fuel surcharge")


class CreateLoadResponseModel(BaseModel):
    """Response model for load creation."""
    load_id: str = Field(..., description="Unique load ID")
    reference_number: str = Field(..., description="Load reference number")
    status: str = Field(..., description="Load status")
    created_at: datetime = Field(..., description="Creation timestamp")


class LoadSummaryModel(BaseModel):
    """Load summary model for list responses."""
    load_id: str = Field(..., description="Unique load ID")
    origin: str = Field(..., description="Origin as 'City, ST'")
    destination: str = Field(..., description="Destination as 'City, ST'")
    pickup_datetime: datetime = Field(..., description="Pickup date and time")
    delivery_datetime: datetime = Field(..., description="Delivery date and time")
    equipment_type: str = Field(..., description="Equipment type")
    loadboard_rate: float = Field(..., description="Loadboard rate")
    notes: Optional[str] = Field(None, description="Notes")
    weight: int = Field(..., description="Weight in pounds")
    commodity_type: str = Field(..., description="Commodity type")
    status: str = Field(..., description="Load status")
    created_at: datetime = Field(..., description="Creation timestamp")


class ListLoadsResponseModel(BaseModel):
    """Response model for load listing."""
    loads: List[LoadSummaryModel] = Field(..., description="List of loads")
    total_count: int = Field(..., description="Total number of loads")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


@router.post("/", response_model=CreateLoadResponseModel, status_code=201)
async def create_load(
    request: CreateLoadRequestModel,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Create a new load in the system.

    Creates a new load with the provided details including origin, destination,
    schedule, equipment requirements, and pricing information.

    Args:
        request: Load creation request with all required fields
        session: Database session dependency

    Returns:
        CreateLoadResponseModel: Created load information with ID and status

    Raises:
        HTTPException: 400 for validation errors, 409 for duplicate reference numbers
    """
    try:
        # Initialize repository and use case
        load_repo = PostgresLoadRepository(session)
        use_case = CreateLoadUseCase(load_repo)

        # Convert request model to use case request
        from src.core.application.use_cases.create_load_use_case import CreateLoadRequest

        origin = Location(
            city=request.origin.city,
            state=request.origin.state,
            zip_code=request.origin.zip
        )

        destination = Location(
            city=request.destination.city,
            state=request.destination.state,
            zip_code=request.destination.zip
        )

        use_case_request = CreateLoadRequest(
            origin=origin,
            destination=destination,
            pickup_datetime=request.pickup_datetime,
            delivery_datetime=request.delivery_datetime,
            equipment_type=request.equipment_type,
            loadboard_rate=request.loadboard_rate,
            weight=request.weight,
            commodity_type=request.commodity_type,
            notes=request.notes,
            reference_number=request.reference_number,
            broker_company=request.broker_company,
            special_requirements=request.special_requirements,
            customer_name=request.customer_name,
            dimensions=request.dimensions,
            pieces=request.pieces,
            hazmat=request.hazmat,
            hazmat_class=request.hazmat_class,
            miles=request.miles,
            fuel_surcharge=request.fuel_surcharge
        )

        # Execute use case
        response = await use_case.execute(use_case_request)

        # Commit the transaction
        await session.commit()

        # Convert to API response
        return CreateLoadResponseModel(
            load_id=response.load_id,
            reference_number=response.reference_number,
            status=response.status,
            created_at=response.created_at
        )

    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        elif "validation" in error_msg.lower() or "required" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")


@router.get("/", response_model=ListLoadsResponseModel)
async def list_loads(
    status: Optional[str] = Query(None, description="Filter by load status (AVAILABLE, BOOKED, etc.)"),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    start_date: Optional[date] = Query(None, description="Filter by pickup date start (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by pickup date end (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    sort_by: str = Query("created_at_desc", description="Sort field and direction"),
    session: AsyncSession = Depends(get_database_session)
):
    """
    List all loads with optional filtering and pagination.

    Retrieves a paginated list of loads with optional filters for status,
    equipment type, and date range.

    Query Parameters:
        - status: Filter by load status (AVAILABLE, BOOKED, IN_TRANSIT, etc.)
        - equipment_type: Filter by equipment type (53-foot van, Flatbed, etc.)
        - start_date: Start date for pickup date filter (YYYY-MM-DD)
        - end_date: End date for pickup date filter (YYYY-MM-DD)
        - page: Page number starting from 1
        - limit: Items per page (1-100, default 20)
        - sort_by: Sort options - created_at_desc, pickup_date_asc, rate_desc, etc.

    Returns:
        ListLoadsResponseModel: Paginated list of loads with metadata

    Raises:
        HTTPException: 400 for validation errors
    """
    try:
        # Initialize repository and use case
        load_repo = PostgresLoadRepository(session)
        use_case = ListLoadsUseCase(load_repo)

        # Convert request parameters to use case request
        from src.core.application.use_cases.list_loads_use_case import ListLoadsRequest

        use_case_request = ListLoadsRequest(
            status=status,
            equipment_type=equipment_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
            sort_by=sort_by
        )

        # Execute use case
        response = await use_case.execute(use_case_request)

        # Convert load summaries to API models
        load_models = [
            LoadSummaryModel(
                load_id=load.load_id,
                origin=load.origin,
                destination=load.destination,
                pickup_datetime=load.pickup_datetime,
                delivery_datetime=load.delivery_datetime,
                equipment_type=load.equipment_type,
                loadboard_rate=load.loadboard_rate,
                notes=load.notes,
                weight=load.weight,
                commodity_type=load.commodity_type,
                status=load.status,
                created_at=load.created_at
            )
            for load in response.loads
        ]

        # Return API response
        return ListLoadsResponseModel(
            loads=load_models,
            total_count=response.total_count,
            page=response.page,
            limit=response.limit,
            has_next=response.has_next,
            has_previous=response.has_previous
        )

    except Exception as e:
        error_msg = str(e)
        if "validation" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")
