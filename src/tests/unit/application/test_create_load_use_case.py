"""
File: test_create_load_use_case.py
Description: Unit tests for CreateLoadUseCase
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

import pytest

from src.core.application.use_cases.create_load_use_case import (
    CreateLoadRequest,
    CreateLoadResponse,
    CreateLoadUseCase,
    DuplicateReferenceException,
    LoadCreationException,
)
from src.core.domain.entities import Load, LoadStatus
from src.core.domain.value_objects import Location
from src.core.ports.repositories import ILoadRepository


class MockLoadRepository(ILoadRepository):
    """Mock repository for testing."""

    def __init__(self):
        self.loads: Dict[UUID, Load] = {}
        self.reference_numbers = set()

    async def create(self, load: Load) -> Load:
        self.loads[load.load_id] = load
        self.reference_numbers.add(load.reference_number)
        return load

    async def get_by_reference_number(self, reference_number: str) -> Optional[Load]:
        for load_value in self.loads.values():
            load: Load = load_value  # Type hint for mypy
            if load.reference_number == reference_number:
                return load
        return None

    async def get_by_id(self, load_id):
        return self.loads.get(load_id)

    async def get_active_by_id(self, load_id):
        load = self.loads.get(load_id)
        if load and load.is_active:
            return load
        return None

    async def update(self, load):
        self.loads[load.load_id] = load
        return load

    async def delete(self, load_id):
        if load_id in self.loads:
            del self.loads[load_id]
            return True
        return False

    async def search_loads(self, criteria):
        return list(self.loads.values())

    async def get_available_loads(self, limit=100, offset=0):
        return list(self.loads.values())

    async def get_loads_by_status(self, status, limit=100, offset=0):
        return [load for load in self.loads.values() if load.status == status]

    async def get_loads_by_carrier(self, carrier_id, limit=100, offset=0):
        return []  # No longer used - removed carrier booking tracking

    async def count_loads_by_criteria(self, criteria):
        return len(self.loads)

    async def get_loads_expiring_soon(self, hours=24):
        return []

    async def get_load_metrics(self, start_date, end_date):
        return {}

    async def list_all(
        self,
        status=None,
        equipment_type=None,
        start_date=None,
        end_date=None,
        limit=20,
        offset=0,
        sort_by="created_at_desc",
    ):
        return list(self.loads.values()), len(self.loads)


@pytest.fixture
def mock_repository():
    return MockLoadRepository()


@pytest.fixture
def create_load_use_case(mock_repository):
    return CreateLoadUseCase(mock_repository)


@pytest.fixture
def valid_create_request():
    origin = Location(city="Chicago", state="IL", zip_code="60601")
    destination = Location(city="Los Angeles", state="CA", zip_code="90210")

    # Use future dates
    from datetime import timedelta

    future_date = datetime.utcnow() + timedelta(days=5)
    delivery_date = future_date + timedelta(days=2)

    return CreateLoadRequest(
        origin=origin,
        destination=destination,
        pickup_datetime=future_date.replace(hour=10, minute=0, second=0, microsecond=0),
        delivery_datetime=delivery_date.replace(
            hour=16, minute=0, second=0, microsecond=0
        ),
        equipment_type="53-foot van",
        loadboard_rate=2500.00,
        weight=25000,
        commodity_type="Electronics",
        notes="Handle with care",
    )


class TestCreateLoadUseCase:
    @pytest.mark.asyncio
    async def test_create_load_success(
        self, create_load_use_case, valid_create_request
    ):
        """Test successful load creation."""
        response = await create_load_use_case.execute(valid_create_request)

        assert isinstance(response, CreateLoadResponse)
        assert response.load_id is not None
        assert response.reference_number is not None
        assert response.reference_number.startswith("LD-2025-")
        assert response.status == LoadStatus.AVAILABLE.value
        assert response.created_at is not None

    @pytest.mark.asyncio
    async def test_create_load_with_custom_reference(
        self, create_load_use_case, valid_create_request
    ):
        """Test load creation with custom reference number."""
        valid_create_request.reference_number = "CUSTOM-REF-001"

        response = await create_load_use_case.execute(valid_create_request)

        assert response.reference_number == "CUSTOM-REF-001"

    @pytest.mark.asyncio
    async def test_create_load_duplicate_reference_fails(
        self, create_load_use_case, valid_create_request, mock_repository
    ):
        """Test that duplicate reference numbers raise exception."""
        valid_create_request.reference_number = "DUPLICATE-REF"

        # First creation should succeed
        await create_load_use_case.execute(valid_create_request)

        # Second creation with same reference should fail
        with pytest.raises(DuplicateReferenceException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_missing_origin_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that missing origin raises exception."""
        valid_create_request.origin = None

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "Origin is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_missing_destination_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that missing destination raises exception."""
        valid_create_request.destination = None

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "Destination is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_invalid_rate_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that negative rate raises exception."""
        valid_create_request.loadboard_rate = -100.0

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_invalid_weight_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that excessive weight raises exception."""
        valid_create_request.weight = 90000  # Over 80k limit

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "cannot exceed 80,000 pounds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_invalid_dates_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that invalid date order raises exception."""
        from datetime import timedelta

        future_date = datetime.utcnow() + timedelta(days=5)
        past_date = future_date - timedelta(days=2)

        valid_create_request.pickup_datetime = future_date
        valid_create_request.delivery_datetime = past_date

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "must be before delivery datetime" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_past_pickup_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that pickup date in the past raises exception."""
        valid_create_request.pickup_datetime = datetime(2020, 1, 1, 10, 0, 0)

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "cannot be in the past" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_load_invalid_equipment_type_fails(
        self, create_load_use_case, valid_create_request
    ):
        """Test that empty equipment type raises exception."""
        valid_create_request.equipment_type = ""  # Empty string should fail

        with pytest.raises(LoadCreationException) as exc_info:
            await create_load_use_case.execute(valid_create_request)

        assert "Invalid equipment type" in str(
            exc_info.value
        ) or "Equipment type" in str(exc_info.value)

    # Hazmat fields are no longer supported - removed for compliance

    # Fuel surcharge fields are no longer supported - removed for compliance

    @pytest.mark.asyncio
    async def test_create_load_with_notes(
        self, create_load_use_case, valid_create_request
    ):
        """Test load creation with notes - the only optional field now allowed."""
        valid_create_request.notes = "Special handling required"

        response = await create_load_use_case.execute(valid_create_request)

        assert response.load_id is not None
        assert response.status == LoadStatus.AVAILABLE.value
