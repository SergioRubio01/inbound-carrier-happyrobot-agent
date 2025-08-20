"""
File: test_update_load_endpoint.py
Description: Integration tests for update load PUT endpoint
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import date, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.infrastructure.database.connection import get_database_session
from src.infrastructure.database.models import LoadModel


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def api_key_headers():
    """API key headers for authenticated requests."""
    return {"X-API-Key": "dev-local-api-key"}


@pytest.fixture
async def sample_load_in_db():
    """Create a sample load in the database."""
    session_gen = get_database_session()
    session = await session_gen.__anext__()

    try:
        load_model = LoadModel(
            load_id=uuid4(),
            reference_number="LD-2024-08-00001",
            origin_city="Los Angeles",
            origin_state="CA",
            origin_zip="90210",
            destination_city="New York",
            destination_state="NY",
            destination_zip="10001",
            pickup_date=date(2024, 8, 25),
            pickup_time_start=datetime.strptime("09:00", "%H:%M").time(),
            delivery_date=date(2024, 8, 27),
            delivery_time_start=datetime.strptime("15:00", "%H:%M").time(),
            equipment_type="53-foot van",
            loadboard_rate=2500.0,
            weight=25000,
            commodity_type="Electronics",
            status="AVAILABLE",
            urgency="NORMAL",
            priority_score=50,
            is_active=True,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(load_model)
        await session.commit()
        await session.refresh(load_model)

        yield load_model

        # Cleanup
        await session.delete(load_model)
        await session.commit()
    finally:
        await session.close()


@pytest.mark.integration
class TestUpdateLoadEndpoint:
    """Integration tests for update load endpoint."""

    async def test_successful_load_update(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test successful load update."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 1,
            "weight": 30000,
            "loadboard_rate": 2750.0,
            "notes": "Updated load information",
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["load_id"] == load_id
        assert result["reference_number"] == sample_load_in_db.reference_number
        assert result["version"] == 2  # Version should be incremented
        assert "updated_at" in result

    async def test_update_with_location_changes(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test update with location changes."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 1,
            "origin": {"city": "Chicago", "state": "IL", "zip": "60601"},
            "destination": {"city": "Miami", "state": "FL", "zip": "33101"},
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["version"] == 2

    async def test_update_with_schedule_changes(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test update with schedule changes."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 1,
            "pickup_datetime": "2024-08-26T10:00:00Z",
            "delivery_datetime": "2024-08-28T16:00:00Z",
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["version"] == 2

    async def test_valid_status_transition(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test valid status transition."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 1, "status": "BOOKED"}  # AVAILABLE -> BOOKED is valid

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "BOOKED"
        assert result["version"] == 2

    async def test_load_not_found(self, client: AsyncClient, api_key_headers):
        """Test load not found error."""
        # Arrange
        non_existent_id = str(uuid4())
        update_data = {"version": 1, "weight": 30000}

        # Act
        response = await client.put(
            f"/api/v1/loads/{non_existent_id}",
            json=update_data,
            headers=api_key_headers,
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_version_conflict(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test version conflict error."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 999, "weight": 30000}  # Wrong version

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 409
        assert "version conflict" in response.json()["detail"].lower()

    async def test_invalid_status_transition(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test invalid status transition."""
        # Arrange - First set load to DELIVERED
        session_gen = get_database_session()
        session = await session_gen.__anext__()
        try:
            load_model = await session.get(LoadModel, sample_load_in_db.load_id)
            load_model.status = "DELIVERED"
            load_model.version = 2
            await session.commit()
        finally:
            await session.close()

        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 2,
            "status": "AVAILABLE",  # DELIVERED -> AVAILABLE is invalid
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 409
        assert "invalid status transition" in response.json()["detail"].lower()

    async def test_cannot_update_delivered_load(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test that delivered loads cannot be updated."""
        # Arrange - First set load to DELIVERED
        session_gen = get_database_session()
        session = await session_gen.__anext__()
        try:
            load_model = await session.get(LoadModel, sample_load_in_db.load_id)
            load_model.status = "DELIVERED"
            await session.commit()
        finally:
            await session.close()

        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 1, "weight": 30000}

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 409
        assert "has been delivered" in response.json()["detail"].lower()

    async def test_validation_errors(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test validation errors."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 1, "loadboard_rate": 0.0}  # Invalid rate

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 400
        assert "must be greater than 0" in response.json()["detail"]

    async def test_invalid_uuid_format(self, client: AsyncClient, api_key_headers):
        """Test invalid UUID format."""
        # Arrange
        invalid_load_id = "not-a-uuid"
        update_data = {"version": 1, "weight": 30000}

        # Act
        response = await client.put(
            f"/api/v1/loads/{invalid_load_id}",
            json=update_data,
            headers=api_key_headers,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    async def test_missing_version_field(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test missing version field."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"weight": 30000}  # Missing version

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 422  # Validation error

    async def test_invalid_equipment_type(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test invalid equipment type."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 1, "equipment_type": "invalid-equipment"}

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 400

    async def test_invalid_date_logic(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test invalid date logic."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 1,
            "pickup_datetime": "2024-08-28T10:00:00Z",
            "delivery_datetime": "2024-08-27T15:00:00Z",  # Before pickup
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 400
        assert "before delivery" in response.json()["detail"].lower()

    async def test_unauthorized_access(self, client: AsyncClient, sample_load_in_db):
        """Test unauthorized access."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {"version": 1, "weight": 30000}

        # Act - No API key
        response = await client.put(f"/api/v1/loads/{load_id}", json=update_data)

        # Assert
        assert response.status_code == 401

    async def test_partial_update_preserves_existing_values(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test that partial updates preserve existing values."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        original_weight = sample_load_in_db.weight

        update_data = {
            "version": 1,
            "notes": "Only updating notes",  # Only updating notes
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["version"] == 2

        # Verify the load still has its original weight by getting it
        get_response = await client.get(
            f"/api/v1/loads/{load_id}", headers=api_key_headers
        )
        assert get_response.status_code == 200
        load_data = get_response.json()
        assert load_data["weight"] == original_weight

    async def test_update_with_all_fields(
        self, client: AsyncClient, sample_load_in_db, api_key_headers
    ):
        """Test comprehensive update with all fields."""
        # Arrange
        load_id = str(sample_load_in_db.load_id)
        update_data = {
            "version": 1,
            "origin": {"city": "Chicago", "state": "IL", "zip": "60601"},
            "destination": {"city": "Miami", "state": "FL", "zip": "33101"},
            "pickup_datetime": "2024-08-26T10:00:00Z",
            "delivery_datetime": "2024-08-28T16:00:00Z",
            "equipment_type": "Flatbed",
            "loadboard_rate": 2800.0,
            "weight": 35000,
            "commodity_type": "Steel",
            "notes": "Updated load with all fields",
            "broker_company": "New Broker LLC",
            "special_requirements": ["Tarps required", "Crane needed"],
            "customer_name": "Updated Customer",
            "dimensions": "48x8x8",
            "pieces": 5,
            "hazmat": True,
            "hazmat_class": "1.1",
            "miles": 1200,
            "fuel_surcharge": 200.0,
            "status": "BOOKED",
            "urgency": "HIGH",
            "priority_score": 85,
            "minimum_rate": 2600.0,
            "maximum_rate": 3000.0,
            "target_rate": 2800.0,
            "auto_accept_threshold": 2900.0,
            "route_notes": "Avoid construction zone",
            "internal_notes": "High priority customer",
        }

        # Act
        response = await client.put(
            f"/api/v1/loads/{load_id}", json=update_data, headers=api_key_headers
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "BOOKED"
        assert result["version"] == 2
