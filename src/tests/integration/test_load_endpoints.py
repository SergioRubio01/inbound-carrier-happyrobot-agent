"""
File: test_load_endpoints.py
Description: Integration tests for load API endpoints
Author: HappyRobot Team
Created: 2024-08-20
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import asyncio

from src.interfaces.api.app import create_app
from src.infrastructure.database.base import Base
from src.interfaces.api.v1.dependencies.database import get_database_session


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_database_session() -> AsyncSession:
    """Override database session for testing."""
    async with TestingSessionLocal() as session:
        yield session


# Create test app without authentication middleware
from fastapi import FastAPI
from src.interfaces.api.v1 import loads

app = FastAPI()
app.include_router(loads.router, prefix="/api/v1")
app.dependency_overrides[get_database_session] = override_get_database_session


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def valid_load_data():
    """Valid load data for testing."""
    from datetime import timedelta
    future_date = datetime.utcnow() + timedelta(days=5)
    delivery_date = future_date + timedelta(days=2)

    return {
        "origin": {
            "city": "Chicago",
            "state": "IL",
            "zip": "60601"
        },
        "destination": {
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90210"
        },
        "pickup_datetime": future_date.replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
        "delivery_datetime": delivery_date.replace(hour=16, minute=0, second=0, microsecond=0).isoformat(),
        "equipment_type": "53-foot van",
        "loadboard_rate": 2500.00,
        "weight": 25000,
        "commodity_type": "Electronics",
        "notes": "Handle with care",
        "broker_company": "Test Broker LLC"
    }


class TestCreateLoadEndpoint:

    def test_create_load_success(self, client, valid_load_data):
        """Test successful load creation."""
        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data
        )

        assert response.status_code == 201
        data = response.json()

        assert "load_id" in data
        assert "reference_number" in data
        assert data["status"] == "AVAILABLE"
        assert "created_at" in data
        assert data["reference_number"].startswith("LD-2025-")

    @pytest.mark.asyncio
    def test_create_load_with_custom_reference(self, client, valid_load_data):
        """Test load creation with custom reference number."""
        valid_load_data["reference_number"] = "CUSTOM-REF-001"

        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reference_number"] == "CUSTOM-REF-001"

    @pytest.mark.asyncio
    async def test_create_load_duplicate_reference_fails(self, client, api_key_headers, valid_load_data, setup_database):
        """Test that duplicate reference numbers fail."""
        valid_load_data["reference_number"] = "DUPLICATE-REF"

        # First creation should succeed
        response1 = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )
        assert response1.status_code == 201

        # Second creation should fail
        response2 = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_load_missing_required_field_fails(self, client, api_key_headers, valid_load_data, setup_database):
        """Test that missing required fields fail."""
        del valid_load_data["origin"]

        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_load_invalid_rate_fails(self, client, api_key_headers, valid_load_data, setup_database):
        """Test that invalid rate fails validation."""
        valid_load_data["loadboard_rate"] = -100.0

        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_load_invalid_weight_fails(self, client, api_key_headers, valid_load_data, setup_database):
        """Test that invalid weight fails validation."""
        valid_load_data["weight"] = 100000  # Over limit

        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_load_invalid_state_fails(self, client, api_key_headers, valid_load_data, setup_database):
        """Test that invalid state codes fail validation."""
        valid_load_data["origin"]["state"] = "INVALID"

        response = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_load_without_api_key_fails(self, client, valid_load_data, setup_database):
        """Test that requests without API key fail."""
        response = client.post("/api/v1/loads/", json=valid_load_data)

        assert response.status_code == 401


class TestListLoadsEndpoint:

    @pytest.mark.asyncio
    async def test_list_loads_success(self, client, api_key_headers, setup_database):
        """Test successful load listing."""
        response = client.get("/api/v1/loads/", headers=api_key_headers)

        assert response.status_code == 200
        data = response.json()

        assert "loads" in data
        assert "total_count" in data
        assert "page" in data
        assert "limit" in data
        assert "has_next" in data
        assert "has_previous" in data

        assert data["page"] == 1
        assert data["limit"] == 20
        assert not data["has_previous"]

    @pytest.mark.asyncio
    async def test_list_loads_with_filters(self, client, api_key_headers, setup_database):
        """Test load listing with query filters."""
        params = {
            "status": "AVAILABLE",
            "equipment_type": "53-foot van",
            "page": 1,
            "limit": 10,
            "sort_by": "created_at_desc"
        }

        response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_loads_with_date_range(self, client, api_key_headers, setup_database):
        """Test load listing with date range filter."""
        params = {
            "start_date": "2024-08-25",
            "end_date": "2024-08-27"
        }

        response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_loads_pagination(self, client, api_key_headers, setup_database):
        """Test load listing pagination."""
        # Test different page sizes
        for page in [1, 2]:
            for limit in [5, 10, 20]:
                params = {"page": page, "limit": limit}
                response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

                assert response.status_code == 200
                data = response.json()

                assert data["page"] == page
                assert data["limit"] == limit

    @pytest.mark.asyncio
    async def test_list_loads_sorting_options(self, client, api_key_headers, setup_database):
        """Test different sorting options."""
        sort_options = [
            "created_at_desc", "created_at_asc",
            "pickup_date_desc", "pickup_date_asc",
            "rate_desc", "rate_asc"
        ]

        for sort_by in sort_options:
            params = {"sort_by": sort_by}
            response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_loads_invalid_page_fails(self, client, api_key_headers, setup_database):
        """Test that invalid page parameter fails."""
        params = {"page": 0}
        response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_loads_invalid_limit_fails(self, client, api_key_headers, setup_database):
        """Test that invalid limit parameter fails."""
        params = {"limit": 200}  # Over max
        response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_loads_invalid_sort_fails(self, client, api_key_headers, setup_database):
        """Test that invalid sort_by parameter fails."""
        params = {"sort_by": "invalid_sort"}
        response = client.get("/api/v1/loads/", params=params, headers=api_key_headers)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_loads_without_api_key_fails(self, client, setup_database):
        """Test that requests without API key fail."""
        response = client.get("/api/v1/loads/")

        assert response.status_code == 401


class TestLoadEndpointsIntegration:

    @pytest.mark.asyncio
    async def test_create_then_list_loads(self, client, api_key_headers, valid_load_data, setup_database):
        """Test creating a load and then listing it."""
        # Create a load
        create_response = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )

        assert create_response.status_code == 201
        created_load = create_response.json()

        # List loads
        list_response = client.get("/api/v1/loads/", headers=api_key_headers)

        assert list_response.status_code == 200
        loads_data = list_response.json()

        # The created load should be in the list
        assert loads_data["total_count"] >= 1

        # Find the created load in the list
        created_load_in_list = None
        for load in loads_data["loads"]:
            if load["load_id"] == created_load["load_id"]:
                created_load_in_list = load
                break

        assert created_load_in_list is not None
        assert created_load_in_list["origin"] == "Chicago, IL"
        assert created_load_in_list["destination"] == "Los Angeles, CA"
        assert created_load_in_list["status"] == "AVAILABLE"

    @pytest.mark.asyncio
    async def test_create_multiple_loads_and_filter(self, client, api_key_headers, valid_load_data, setup_database):
        """Test creating multiple loads and filtering them."""
        # Create first load (53-foot van)
        response1 = client.post(
            "/api/v1/loads/",
            json=valid_load_data,
            headers=api_key_headers
        )
        assert response1.status_code == 201

        # Create second load (Reefer)
        reefer_data = valid_load_data.copy()
        reefer_data["equipment_type"] = "Reefer"
        reefer_data["commodity_type"] = "Frozen Foods"

        response2 = client.post(
            "/api/v1/loads/",
            json=reefer_data,
            headers=api_key_headers
        )
        assert response2.status_code == 201

        # List all loads
        all_loads_response = client.get("/api/v1/loads/", headers=api_key_headers)
        assert all_loads_response.status_code == 200
        all_loads = all_loads_response.json()
        assert all_loads["total_count"] >= 2

        # Filter by equipment type (53-foot van)
        van_loads_response = client.get(
            "/api/v1/loads/",
            params={"equipment_type": "53-foot van"},
            headers=api_key_headers
        )
        assert van_loads_response.status_code == 200
        van_loads = van_loads_response.json()
        assert van_loads["total_count"] >= 1

        # All returned loads should be 53-foot van
        for load in van_loads["loads"]:
            assert load["equipment_type"] == "53-foot van"

        # Filter by equipment type (Reefer)
        reefer_loads_response = client.get(
            "/api/v1/loads/",
            params={"equipment_type": "Reefer"},
            headers=api_key_headers
        )
        assert reefer_loads_response.status_code == 200
        reefer_loads = reefer_loads_response.json()
        assert reefer_loads["total_count"] >= 1

        # All returned loads should be Reefer
        for load in reefer_loads["loads"]:
            assert load["equipment_type"] == "Reefer"
