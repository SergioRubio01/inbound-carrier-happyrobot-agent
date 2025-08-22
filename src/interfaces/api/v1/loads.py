"""
File: loads.py
Description: Load management API endpoints
Author: HappyRobot Team
Created: 2024-08-14
Updated: 2024-08-20
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Configuration
from src.config.settings import settings

# Use cases
from src.core.application.use_cases.create_load_use_case import CreateLoadUseCase
from src.core.application.use_cases.delete_load_use_case import DeleteLoadUseCase
from src.core.application.use_cases.list_loads_use_case import ListLoadsUseCase
from src.core.application.use_cases.update_load_use_case import UpdateLoadUseCase

# Domain objects
from src.core.domain.value_objects import Location
from src.infrastructure.database.postgres import PostgresLoadRepository

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session

router = APIRouter(prefix="/loads", tags=["Loads"])


class LocationRequestModel(BaseModel):
    """Location model for requests."""

    city: str = Field(..., description="City name", min_length=1)
    state: str = Field(
        ..., description="2-letter state code", min_length=2, max_length=2
    )
    zip: Optional[str] = Field(None, description="ZIP code")


class CreateLoadRequestModel(BaseModel):
    """Request model for creating a new load."""

    origin: LocationRequestModel = Field(..., description="Load origin location")
    destination: LocationRequestModel = Field(
        ..., description="Load destination location"
    )
    pickup_datetime: datetime = Field(..., description="Pickup date and time")
    delivery_datetime: datetime = Field(..., description="Delivery date and time")
    equipment_type: str = Field(..., description="Required equipment type")
    loadboard_rate: float = Field(..., gt=0, description="Loadboard rate in USD")
    weight: int = Field(
        ..., gt=0, le=settings.max_load_weight_lbs, description="Weight in pounds"
    )
    commodity_type: str = Field(..., description="Type of commodity")
    notes: Optional[str] = Field(None, description="Additional notes")
    dimensions: Optional[str] = Field(None, description="Load dimensions")
    num_of_pieces: Optional[int] = Field(None, ge=0, description="Number of pieces")
    miles: Optional[str] = Field(None, description="Distance in miles")
    booked: Optional[bool] = Field(False, description="Is load booked")
    session_id: Optional[str] = Field(None, description="Session identifier")


class CreateLoadResponseModel(BaseModel):
    """Response model for load creation."""

    load_id: str = Field(..., description="Unique load ID")
    reference_number: str = Field(..., description="Load reference number")
    booked: bool = Field(..., description="Is load booked")
    created_at: datetime = Field(..., description="Creation timestamp")


class UpdateLoadRequestModel(BaseModel):
    """Request model for updating an existing load."""

    origin: Optional[LocationRequestModel] = Field(
        None, description="Load origin location"
    )
    destination: Optional[LocationRequestModel] = Field(
        None, description="Load destination location"
    )
    pickup_datetime: Optional[datetime] = Field(
        None, description="Pickup date and time"
    )
    delivery_datetime: Optional[datetime] = Field(
        None, description="Delivery date and time"
    )
    equipment_type: Optional[str] = Field(None, description="Required equipment type")
    loadboard_rate: Optional[float] = Field(
        None, gt=0, description="Loadboard rate in USD"
    )
    weight: Optional[int] = Field(
        None, gt=0, le=settings.max_load_weight_lbs, description="Weight in pounds"
    )
    commodity_type: Optional[str] = Field(None, description="Type of commodity")
    notes: Optional[str] = Field(None, description="Additional notes")
    dimensions: Optional[str] = Field(None, description="Load dimensions")
    num_of_pieces: Optional[int] = Field(None, ge=0, description="Number of pieces")
    miles: Optional[str] = Field(None, description="Distance in miles")
    booked: Optional[bool] = Field(None, description="Is load booked")
    session_id: Optional[str] = Field(None, description="Session identifier")


class UpdateLoadResponseModel(BaseModel):
    """Response model for load update."""

    load_id: str = Field(..., description="Unique load ID")
    reference_number: Optional[str] = Field(None, description="Load reference number")
    booked: bool = Field(..., description="Is load booked")
    updated_at: datetime = Field(..., description="Update timestamp")
    # Include all potentially updated fields
    origin: Optional[str] = Field(None, description="Updated origin as 'City, ST'")
    destination: Optional[str] = Field(
        None, description="Updated destination as 'City, ST'"
    )
    pickup_datetime: Optional[datetime] = Field(
        None, description="Updated pickup date and time"
    )
    delivery_datetime: Optional[datetime] = Field(
        None, description="Updated delivery date and time"
    )
    equipment_type: Optional[str] = Field(None, description="Updated equipment type")
    loadboard_rate: Optional[float] = Field(None, description="Updated loadboard rate")
    weight: Optional[int] = Field(None, description="Updated weight in pounds")
    commodity_type: Optional[str] = Field(None, description="Updated commodity type")
    notes: Optional[str] = Field(None, description="Updated notes")
    dimensions: Optional[str] = Field(None, description="Updated dimensions")
    num_of_pieces: Optional[int] = Field(None, description="Updated number of pieces")
    miles: Optional[str] = Field(None, description="Updated miles")
    session_id: Optional[str] = Field(None, description="Updated session ID")
    modified_fields: Optional[List[str]] = Field(
        None, description="List of fields that were modified"
    )


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
    booked: bool = Field(..., description="Is load booked")
    created_at: datetime = Field(..., description="Creation timestamp")
    dimensions: Optional[str] = Field(None, description="Load dimensions")
    num_of_pieces: Optional[int] = Field(None, description="Number of pieces")
    miles: Optional[str] = Field(None, description="Distance in miles")
    session_id: Optional[str] = Field(None, description="Session identifier")


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
    session: AsyncSession = Depends(get_database_session),
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
        from src.core.application.use_cases.create_load_use_case import (
            CreateLoadRequest,
        )

        origin = Location(
            city=request.origin.city,
            state=request.origin.state,
            zip_code=request.origin.zip,
        )

        destination = Location(
            city=request.destination.city,
            state=request.destination.state,
            zip_code=request.destination.zip,
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
            dimensions=request.dimensions,
            num_of_pieces=request.num_of_pieces,
            miles=request.miles,
            booked=request.booked,
            session_id=request.session_id,
        )

        # Execute use case
        response = await use_case.execute(use_case_request)

        # Commit the transaction
        await session.commit()

        # Convert to API response
        return CreateLoadResponseModel(
            load_id=response.load_id,
            reference_number=response.reference_number,
            booked=response.booked,
            created_at=response.created_at,
        )

    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        elif "validation" in error_msg.lower() or "required" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {error_msg}"
            )


@router.get("/", response_model=ListLoadsResponseModel)
async def list_loads(
    booked: Optional[bool] = Query(
        None, description="Filter by booked status (true/false)"
    ),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    start_date: Optional[date] = Query(
        None, description="Filter by pickup date start (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None, description="Filter by pickup date end (YYYY-MM-DD)"
    ),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of items per page (max 100)"
    ),
    sort_by: str = Query("created_at_desc", description="Sort field and direction"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    List all loads with optional filtering and pagination.

    Retrieves a paginated list of loads with optional filters for status,
    equipment type, and date range.

    Query Parameters:
        - booked: Filter by booked status (true/false)
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
            booked=booked,
            equipment_type=equipment_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
            sort_by=sort_by,
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
                booked=load.booked,
                created_at=load.created_at,
                dimensions=load.dimensions,
                num_of_pieces=load.num_of_pieces,
                miles=load.miles,
                session_id=load.session_id,
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
            has_previous=response.has_previous,
        )

    except Exception as e:
        error_msg = str(e)
        if "validation" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {error_msg}"
            )


@router.get("/{load_id}", response_model=LoadSummaryModel)
async def get_load_by_id(
    load_id: UUID = Path(..., description="Load ID"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Get a single load by its ID.

    Retrieves detailed information about a specific load using its unique identifier.
    Only returns active (non-deleted) loads.

    Args:
        load_id: The unique identifier of the load
        session: Database session dependency

    Returns:
        LoadSummaryModel: Load information

    Raises:
        HTTPException: 404 if load not found, 500 for server errors
    """
    try:
        # Initialize repository
        load_repo = PostgresLoadRepository(session)

        # Get the load (only active loads)
        load = await load_repo.get_active_by_id(load_id)
        if not load:
            raise HTTPException(
                status_code=404, detail=f"Load with ID {load_id} not found"
            )

        # Convert to load summary using the same logic as in list_loads
        pickup_datetime = datetime.combine(
            load.pickup_date or date.today(),
            load.pickup_time_start or datetime.min.time(),
        )

        delivery_datetime = datetime.combine(
            load.delivery_date or date.today(),
            load.delivery_time_start or datetime.min.time(),
        )

        # Handle optional fields with safe access
        origin_str = ""
        if load.origin:
            origin_str = f"{load.origin.city}, {load.origin.state}"

        destination_str = ""
        if load.destination:
            destination_str = f"{load.destination.city}, {load.destination.state}"

        equipment_type_name = ""
        if load.equipment_type:
            equipment_type_name = load.equipment_type.name

        loadboard_rate_float = 0.0
        if load.loadboard_rate:
            loadboard_rate_float = load.loadboard_rate.to_float()

        return LoadSummaryModel(
            load_id=str(load.load_id),
            origin=origin_str,
            destination=destination_str,
            pickup_datetime=pickup_datetime,
            delivery_datetime=delivery_datetime,
            equipment_type=equipment_type_name,
            loadboard_rate=loadboard_rate_float,
            notes=load.notes,
            weight=load.weight,
            commodity_type=load.commodity_type or "",
            booked=load.booked,
            created_at=load.created_at,
            dimensions=load.dimensions,
            num_of_pieces=load.num_of_pieces,
            miles=load.miles,
            session_id=load.session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{load_id}", status_code=204)
async def delete_load(
    load_id: UUID = Path(..., description="Load ID"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Delete a load by its ID.

    Performs a soft delete of the specified load. Business rules apply:
    - Cannot delete loads that are already deleted
    - Cannot delete inactive loads

    Args:
        load_id: The unique identifier of the load to delete
        session: Database session dependency

    Returns:
        No content (204 status code)

    Raises:
        HTTPException: 404 if load not found, 409 for business rule violations, 500 for server errors
    """
    try:
        # Initialize repository and use case
        load_repo = PostgresLoadRepository(session)
        use_case = DeleteLoadUseCase(load_repo)

        # Convert request to use case request
        from src.core.application.use_cases.delete_load_use_case import (
            DeleteLoadRequest,
        )

        use_case_request = DeleteLoadRequest(load_id=load_id)

        # Execute use case
        await use_case.execute(use_case_request)

        # Commit the transaction
        await session.commit()

        # Return 204 No Content
        return

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif any(
            phrase in error_msg.lower()
            for phrase in [
                "cannot delete",
                "already deleted",
                "not active",
            ]
        ):
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {error_msg}"
            )


@router.put("/{load_id}", response_model=UpdateLoadResponseModel)
@router.post("/{load_id}", response_model=UpdateLoadResponseModel)
@router.patch("/{load_id}", response_model=UpdateLoadResponseModel)
async def update_load(
    request: UpdateLoadRequestModel,
    load_id: UUID = Path(..., description="Load ID"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Update an existing load by its ID.

    Updates an existing load with the provided details. Supports partial updates
    where only specified fields are changed.

    Business rules apply:
    - Cannot update inactive loads
    - Booked status can be updated directly (true/false)

    Args:
        load_id: The unique identifier of the load to update
        request: Update request with optional field changes
        session: Database session dependency

    Returns:
        UpdateLoadResponseModel: Updated load information

    Raises:
        HTTPException:
            - 404 if load not found
            - 409 for business rule violations
            - 400 for validation errors
            - 500 for server errors
    """
    try:
        # Initialize repository and use case
        load_repo = PostgresLoadRepository(session)
        use_case = UpdateLoadUseCase(load_repo)

        # Convert request model to use case request
        from src.core.application.use_cases.update_load_use_case import (
            UpdateLoadRequest,
        )

        # Convert locations if provided
        origin = None
        if request.origin:
            origin = Location(
                city=request.origin.city,
                state=request.origin.state,
                zip_code=request.origin.zip,
            )

        destination = None
        if request.destination:
            destination = Location(
                city=request.destination.city,
                state=request.destination.state,
                zip_code=request.destination.zip,
            )

        use_case_request = UpdateLoadRequest(
            load_id=load_id,
            origin=origin,
            destination=destination,
            pickup_datetime=request.pickup_datetime,
            delivery_datetime=request.delivery_datetime,
            equipment_type=request.equipment_type,
            loadboard_rate=request.loadboard_rate,
            weight=request.weight,
            commodity_type=request.commodity_type,
            notes=request.notes,
            dimensions=request.dimensions,
            num_of_pieces=request.num_of_pieces,
            miles=request.miles,
            booked=request.booked,
            session_id=request.session_id,
        )

        # Execute use case
        response = await use_case.execute(use_case_request)

        # Commit the transaction
        await session.commit()

        # Convert to API response with all modified fields
        api_response = UpdateLoadResponseModel(
            load_id=response.load_id,
            reference_number=response.reference_number,
            booked=response.booked,
            updated_at=response.updated_at,
            modified_fields=response.modified_fields,
        )

        # Add all the modified field values to the response
        if response.origin:
            api_response.origin = response.origin
        if response.destination:
            api_response.destination = response.destination
        if response.pickup_datetime:
            api_response.pickup_datetime = response.pickup_datetime
        if response.delivery_datetime:
            api_response.delivery_datetime = response.delivery_datetime
        if response.equipment_type:
            api_response.equipment_type = response.equipment_type
        if response.loadboard_rate is not None:
            api_response.loadboard_rate = response.loadboard_rate
        if response.weight is not None:
            api_response.weight = response.weight
        if response.commodity_type:
            api_response.commodity_type = response.commodity_type
        if response.notes is not None:
            api_response.notes = response.notes
        if response.dimensions is not None:
            api_response.dimensions = response.dimensions
        if response.num_of_pieces is not None:
            api_response.num_of_pieces = response.num_of_pieces
        if response.miles is not None:
            api_response.miles = response.miles
        if response.session_id is not None:
            api_response.session_id = response.session_id

        return api_response

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif any(
            phrase in error_msg.lower()
            for phrase in [
                "cannot update",
                "not active",
            ]
        ):
            raise HTTPException(status_code=409, detail=error_msg)
        elif (
            "validation" in error_msg.lower()
            or "required" in error_msg.lower()
            or "must be" in error_msg.lower()
        ):
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {error_msg}"
            )
