"""
File: test_delete_load_use_case.py
Description: Unit tests for delete load use case
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.application.use_cases.delete_load_use_case import (
    DeleteLoadRequest,
    DeleteLoadResponse,
    DeleteLoadUseCase,
    LoadDeletionException,
    LoadNotFoundException,
)
from src.core.domain.entities import Load
from src.core.domain.value_objects import EquipmentType, Location, Rate


class TestDeleteLoadUseCase:
    """Test cases for DeleteLoadUseCase."""

    @pytest.fixture
    def mock_load_repository(self):
        """Create a mock load repository."""
        return AsyncMock()

    @pytest.fixture
    def delete_use_case(self, mock_load_repository):
        """Create a delete use case with mocked dependencies."""
        return DeleteLoadUseCase(mock_load_repository)

    @pytest.fixture
    def sample_load(self):
        """Create a sample load for testing."""
        origin = Location(city="Los Angeles", state="CA", zip_code="90210")
        destination = Location(city="New York", state="NY", zip_code="10001")
        equipment_type = EquipmentType.from_name("53-foot van")
        rate = Rate.from_float(2500.0)

        return Load(
            load_id=uuid4(),
            reference_number="LD-2024-08-00001",
            origin=origin,
            destination=destination,
            pickup_date=datetime.now().date(),
            delivery_date=datetime.now().date(),
            equipment_type=equipment_type,
            loadboard_rate=rate,
            weight=40000,
            commodity_type="General Freight",
            booked=False,
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_delete_load_success(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test successful load deletion."""
        # Arrange
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = True

        request = DeleteLoadRequest(load_id=load_id)

        # Act
        response = await delete_use_case.execute(request)

        # Assert
        assert isinstance(response, DeleteLoadResponse)
        assert response.load_id == str(load_id)
        assert response.reference_number == sample_load.reference_number
        assert isinstance(response.deleted_at, datetime)

        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)

    @pytest.mark.asyncio
    async def test_delete_load_not_found(self, delete_use_case, mock_load_repository):
        """Test deletion of non-existent load."""
        # Arrange
        load_id = uuid4()
        mock_load_repository.get_by_id.return_value = None

        request = DeleteLoadRequest(load_id=load_id)

        # Act & Assert
        with pytest.raises(LoadNotFoundException) as exc_info:
            await delete_use_case.execute(request)

        assert f"Load with ID {load_id} not found" in str(exc_info.value)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_load_with_booked_status_succeeds(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test deletion of booked load succeeds."""
        # Arrange
        sample_load.booked = True
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = True

        request = DeleteLoadRequest(load_id=load_id)

        # Act
        response = await delete_use_case.execute(request)

        # Assert
        assert isinstance(response, DeleteLoadResponse)
        assert response.load_id == str(load_id)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)

    @pytest.mark.asyncio
    async def test_delete_load_not_booked_succeeds(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test deletion of not booked load succeeds."""
        # Arrange
        sample_load.booked = False
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = True

        request = DeleteLoadRequest(load_id=load_id)

        # Act
        response = await delete_use_case.execute(request)

        # Assert
        assert isinstance(response, DeleteLoadResponse)
        assert response.load_id == str(load_id)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)

    @pytest.mark.asyncio
    async def test_delete_already_deleted_load_succeeds(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test deletion of already deleted load succeeds (idempotent operation)."""
        # Arrange - Set the load as inactive to simulate a deleted state
        sample_load.is_active = False
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = True

        request = DeleteLoadRequest(load_id=load_id)

        # Act
        response = await delete_use_case.execute(request)

        # Assert
        assert isinstance(response, DeleteLoadResponse)
        assert response.load_id == str(load_id)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)

    @pytest.mark.asyncio
    async def test_delete_inactive_load_succeeds(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test deletion of inactive load succeeds."""
        # Arrange
        sample_load.is_active = False
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = True

        request = DeleteLoadRequest(load_id=load_id)

        # Act
        response = await delete_use_case.execute(request)

        # Assert
        assert isinstance(response, DeleteLoadResponse)
        assert response.load_id == str(load_id)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)

    @pytest.mark.asyncio
    async def test_delete_repository_failure(
        self, delete_use_case, mock_load_repository, sample_load
    ):
        """Test handling of repository deletion failure."""
        # Arrange
        load_id = sample_load.load_id
        mock_load_repository.get_by_id.return_value = sample_load
        mock_load_repository.delete.return_value = False

        request = DeleteLoadRequest(load_id=load_id)

        # Act & Assert
        with pytest.raises(LoadDeletionException) as exc_info:
            await delete_use_case.execute(request)

        assert f"Failed to delete load {load_id}" in str(exc_info.value)
        mock_load_repository.get_by_id.assert_called_once_with(load_id)
        mock_load_repository.delete.assert_called_once_with(load_id)
