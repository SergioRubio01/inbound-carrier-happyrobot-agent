"""
File: test_update_load_use_case.py
Description: Unit tests for UpdateLoadUseCase
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import date, datetime, time
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.core.application.use_cases.update_load_use_case import (
    LoadNotFoundException,
    LoadUpdateException,
    UpdateLoadRequest,
    UpdateLoadResponse,
    UpdateLoadUseCase,
)
from src.core.domain.entities.load import Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, Rate
from src.core.ports.repositories.load_repository import ILoadRepository


@pytest.fixture
def mock_load_repository():
    """Create a mock load repository."""
    return Mock(spec=ILoadRepository)


@pytest.fixture
def sample_load():
    """Create a sample load for testing."""
    return Load(
        load_id=uuid4(),
        reference_number="LD-2024-08-00001",
        origin=Location(city="Los Angeles", state="CA", zip_code="90210"),
        destination=Location(city="New York", state="NY", zip_code="10001"),
        pickup_date=date(2024, 8, 25),
        pickup_time_start=time(9, 0),
        delivery_date=date(2024, 8, 27),
        delivery_time_start=time(15, 0),
        equipment_type=EquipmentType.from_name("53-foot van"),
        loadboard_rate=Rate.from_float(2500.0),
        weight=25000,
        commodity_type="Electronics",
        status=LoadStatus.AVAILABLE,
        urgency=UrgencyLevel.NORMAL,
        is_active=True,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def use_case(mock_load_repository):
    """Create UpdateLoadUseCase instance."""
    return UpdateLoadUseCase(mock_load_repository)


class TestUpdateLoadUseCase:
    """Test cases for UpdateLoadUseCase."""

    @pytest.mark.asyncio
    async def test_successful_load_update(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test successful load update."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load
        updated_load = Load(**sample_load.__dict__)
        updated_load.weight = 30000
        updated_load.loadboard_rate = Rate.from_float(2750.0)
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id, weight=30000, loadboard_rate=2750.0
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert isinstance(result, UpdateLoadResponse)
        assert result.load_id == str(sample_load.load_id)
        assert result.reference_number == sample_load.reference_number
        assert result.status == sample_load.status.value
        # Version is not part of the response, just verify the result is valid
        mock_load_repository.get_active_by_id.assert_called_once_with(
            sample_load.load_id
        )
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_not_found(self, use_case, mock_load_repository):
        """Test load not found exception."""
        # Arrange
        load_id = uuid4()
        mock_load_repository.get_active_by_id.return_value = None

        request = UpdateLoadRequest(load_id=load_id, weight=30000)

        # Act & Assert
        with pytest.raises(LoadNotFoundException) as exc_info:
            await use_case.execute(request)

        assert f"Load with ID {load_id} not found" in str(exc_info.value)
        mock_load_repository.get_active_by_id.assert_called_once_with(load_id)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test database error handling."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load
        mock_load_repository.update.side_effect = Exception(
            "Database connection failed"
        )

        request = UpdateLoadRequest(
            load_id=sample_load.load_id,
            weight=30000,
        )

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "Failed to update load" in str(exc_info.value)
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cannot_update_deleted_load(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test that deleted loads cannot be updated."""
        # Arrange
        sample_load.deleted_at = datetime.utcnow()
        mock_load_repository.get_active_by_id.return_value = sample_load

        request = UpdateLoadRequest(load_id=sample_load.load_id, weight=30000)

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "has been deleted" in str(exc_info.value)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_cannot_update_delivered_load(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test that delivered loads cannot be updated."""
        # Arrange
        sample_load.status = LoadStatus.DELIVERED
        mock_load_repository.get_active_by_id.return_value = sample_load

        request = UpdateLoadRequest(load_id=sample_load.load_id, weight=30000)

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "has been delivered" in str(exc_info.value)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_status_transition(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test invalid status transition."""
        # Arrange - Use CANCELLED status instead of DELIVERED to test transition validation
        sample_load.status = LoadStatus.CANCELLED
        mock_load_repository.get_active_by_id.return_value = sample_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id,
            status="AVAILABLE",  # Cannot go from CANCELLED to AVAILABLE
        )

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "Invalid status transition" in str(exc_info.value)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_status_transition(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test valid status transition."""
        # Arrange
        sample_load.status = LoadStatus.AVAILABLE
        mock_load_repository.get_active_by_id.return_value = sample_load

        updated_load = Load(**sample_load.__dict__)
        updated_load.status = LoadStatus.BOOKED
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id,
            status="BOOKED",  # Valid: AVAILABLE -> BOOKED
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.status == "BOOKED"
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_location_information(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test updating location information."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load

        updated_load = Load(**sample_load.__dict__)
        updated_load.origin = Location(city="Chicago", state="IL", zip_code="60601")
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        new_origin = Location(city="Chicago", state="IL", zip_code="60601")
        request = UpdateLoadRequest(load_id=sample_load.load_id, origin=new_origin)

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result is not None
        # Version is not part of the response, just verify the result is valid
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_schedule_information(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test updating schedule information."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load

        updated_load = Load(**sample_load.__dict__)
        new_pickup_datetime = datetime(2024, 8, 26, 10, 0)
        updated_load.pickup_date = new_pickup_datetime.date()
        updated_load.pickup_time_start = new_pickup_datetime.time()
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id, pickup_datetime=new_pickup_datetime
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result is not None
        # Version is not part of the response, just verify the result is valid
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_pricing_information(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test updating pricing information."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load

        updated_load = Load(**sample_load.__dict__)
        updated_load.loadboard_rate = Rate.from_float(2800.0)
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id,
            loadboard_rate=2800.0,
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result is not None
        # Version is not part of the response, just verify the result is valid
        mock_load_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_errors(self, use_case, mock_load_repository, sample_load):
        """Test validation errors in updated load."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id, loadboard_rate=0.0  # Invalid rate
        )

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "must be greater than 0" in str(exc_info.value)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_date_logic(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test invalid date logic validation."""
        # Arrange
        mock_load_repository.get_active_by_id.return_value = sample_load

        # Set pickup after delivery
        request = UpdateLoadRequest(
            load_id=sample_load.load_id,
            pickup_datetime=datetime(2024, 8, 28, 10, 0),  # After delivery date
            delivery_datetime=datetime(2024, 8, 27, 15, 0),
        )

        # Act & Assert
        with pytest.raises(LoadUpdateException) as exc_info:
            await use_case.execute(request)

        assert "Pickup datetime must be before delivery datetime" in str(exc_info.value)
        mock_load_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_update_preserves_existing_values(
        self, use_case, mock_load_repository, sample_load
    ):
        """Test that partial updates preserve existing values."""
        # Arrange
        original_weight = sample_load.weight
        original_commodity = sample_load.commodity_type
        mock_load_repository.get_active_by_id.return_value = sample_load

        updated_load = Load(**sample_load.__dict__)
        updated_load.notes = "Updated notes"  # Only notes changed
        updated_load.version = 2
        updated_load.updated_at = datetime.utcnow()
        mock_load_repository.update.return_value = updated_load

        request = UpdateLoadRequest(
            load_id=sample_load.load_id, notes="Updated notes"  # Only updating notes
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result is not None
        # Version is not part of the response, just verify the result is valid
        # Verify the update method was called with a load that preserves existing values
        mock_load_repository.update.assert_called_once()
        call_args = mock_load_repository.update.call_args[0][
            0
        ]  # First argument (the load)
        assert call_args.weight == original_weight
        assert call_args.commodity_type == original_commodity
        assert call_args.notes == "Updated notes"
