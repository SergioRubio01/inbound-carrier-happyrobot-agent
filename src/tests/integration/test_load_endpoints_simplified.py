"""
File: test_load_endpoints_simplified.py
Description: Simplified integration tests for load API endpoints
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a simple test app without middleware
from src.interfaces.api.v1 import loads

app = FastAPI()
app.include_router(loads.router, prefix="/api/v1")


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def valid_load_data():
    """Valid load data for testing."""
    future_date = datetime.utcnow() + timedelta(days=5)
    delivery_date = future_date + timedelta(days=2)

    return {
        "origin": {"city": "Chicago", "state": "IL", "zip": "60601"},
        "destination": {"city": "Los Angeles", "state": "CA", "zip": "90210"},
        "pickup_datetime": future_date.replace(
            hour=10, minute=0, second=0, microsecond=0
        ).isoformat(),
        "delivery_datetime": delivery_date.replace(
            hour=16, minute=0, second=0, microsecond=0
        ).isoformat(),
        "equipment_type": "53-foot van",
        "loadboard_rate": 2500.00,
        "weight": 25000,
        "commodity_type": "Electronics",
        "notes": "Handle with care",
        "broker_company": "Test Broker LLC",
    }


def test_create_load_success(client, valid_load_data):
    """Test successful load creation."""
    response = client.post("/api/v1/loads/", json=valid_load_data)

    assert response.status_code == 201
    data = response.json()

    assert "load_id" in data
    assert "reference_number" in data
    assert data["status"] == "AVAILABLE"
    assert "created_at" in data
    assert data["reference_number"].startswith("LD-2025-")


def test_list_loads_success(client):
    """Test successful load listing."""
    response = client.get("/api/v1/loads/")

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


def test_create_load_missing_required_field_fails(client, valid_load_data):
    """Test that missing required fields fail."""
    del valid_load_data["origin"]

    response = client.post("/api/v1/loads/", json=valid_load_data)

    assert response.status_code == 422  # Validation error


def test_list_loads_with_filters(client):
    """Test load listing with query filters."""
    params = {
        "status": "AVAILABLE",
        "equipment_type": "53-foot van",
        "page": 1,
        "limit": 10,
        "sort_by": "created_at_desc",
    }

    response = client.get("/api/v1/loads/", params=params)

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 10


def test_list_loads_invalid_page_fails(client):
    """Test that invalid page parameter fails."""
    params = {"page": 0}
    response = client.get("/api/v1/loads/", params=params)

    assert response.status_code == 422
