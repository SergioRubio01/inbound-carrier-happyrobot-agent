"""
File: test_delete_load_endpoint.py
Description: Integration tests for load DELETE API endpoint
Author: HappyRobot Team
Created: 2024-08-20
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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


@pytest.fixture
def api_key_headers():
    """API key headers for authenticated requests."""
    return {"X-API-Key": "dev-local-api-key"}


@pytest.mark.integration
def test_delete_load_success(client, setup_database, valid_load_data, api_key_headers):
    """Test successful load deletion."""
    create_response = client.post(
        "/api/v1/loads/", json=valid_load_data, headers=api_key_headers
    )

    assert create_response.status_code == 201
    created_load = create_response.json()
    load_id = created_load["load_id"]

    delete_response = client.delete(f"/api/v1/loads/{load_id}", headers=api_key_headers)

    assert delete_response.status_code == 204
    assert delete_response.text == ""


@pytest.mark.integration
def test_delete_load_not_found(client, setup_database, api_key_headers):
    """Test deleting non-existent load returns 404."""
    non_existent_id = str(uuid4())

    delete_response = client.delete(
        f"/api/v1/loads/{non_existent_id}", headers=api_key_headers
    )

    assert delete_response.status_code == 404
    response_data = delete_response.json()
    assert "not found" in response_data["detail"].lower()


@pytest.mark.integration
def test_delete_load_invalid_id(client, setup_database, api_key_headers):
    """Test deleting with invalid UUID format returns 422."""
    invalid_id = "not-a-uuid"

    delete_response = client.delete(
        f"/api/v1/loads/{invalid_id}", headers=api_key_headers
    )

    assert delete_response.status_code == 422


@pytest.mark.integration
def test_delete_load_unauthorized(client, setup_database, valid_load_data):
    """Test deleting without API key returns 401."""
    create_response = client.post(
        "/api/v1/loads/",
        json=valid_load_data,
        headers={"X-API-Key": "dev-local-api-key"},
    )

    assert create_response.status_code == 201
    created_load = create_response.json()
    load_id = created_load["load_id"]

    delete_response = client.delete(f"/api/v1/loads/{load_id}")

    assert delete_response.status_code == 401


@pytest.mark.integration
def test_delete_load_idempotency(
    client, setup_database, valid_load_data, api_key_headers
):
    """Test deleting same load twice."""
    create_response = client.post(
        "/api/v1/loads/", json=valid_load_data, headers=api_key_headers
    )

    assert create_response.status_code == 201
    created_load = create_response.json()
    load_id = created_load["load_id"]

    first_delete_response = client.delete(
        f"/api/v1/loads/{load_id}", headers=api_key_headers
    )

    assert first_delete_response.status_code == 204

    second_delete_response = client.delete(
        f"/api/v1/loads/{load_id}", headers=api_key_headers
    )

    assert second_delete_response.status_code == 404


@pytest.mark.integration
def test_get_load_by_id_success(
    client, setup_database, valid_load_data, api_key_headers
):
    """Test successfully retrieving a load by ID."""
    create_response = client.post(
        "/api/v1/loads/", json=valid_load_data, headers=api_key_headers
    )

    assert create_response.status_code == 201
    created_load = create_response.json()
    load_id = created_load["load_id"]

    get_response = client.get(f"/api/v1/loads/{load_id}", headers=api_key_headers)

    assert get_response.status_code == 200
    load_data = get_response.json()

    assert load_data["load_id"] == load_id
    assert load_data["origin"] == "Chicago, IL"
    assert load_data["destination"] == "Los Angeles, CA"
    assert load_data["equipment_type"] == "53-foot van"
    assert load_data["loadboard_rate"] == 2500.00
    assert load_data["weight"] == 25000
    assert load_data["commodity_type"] == "Electronics"
    assert load_data["status"] == "AVAILABLE"


@pytest.mark.integration
def test_get_deleted_load_returns_404(
    client, setup_database, valid_load_data, api_key_headers
):
    """Test that getting a deleted load returns 404."""
    create_response = client.post(
        "/api/v1/loads/", json=valid_load_data, headers=api_key_headers
    )

    assert create_response.status_code == 201
    created_load = create_response.json()
    load_id = created_load["load_id"]

    delete_response = client.delete(f"/api/v1/loads/{load_id}", headers=api_key_headers)

    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/loads/{load_id}", headers=api_key_headers)

    assert get_response.status_code == 404
    response_data = get_response.json()
    assert "not found" in response_data["detail"].lower()
