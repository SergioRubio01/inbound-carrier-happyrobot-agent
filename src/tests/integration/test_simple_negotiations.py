"""Integration tests for simple negotiations endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.app import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_headers():
    """Valid API headers."""
    return {"X-API-Key": "dev-local-api-key"}


class TestSimpleNegotiations:
    """Test the simple negotiations endpoint."""

    def test_successful_negotiation_round_1(
        self, client: TestClient, valid_headers: dict
    ):
        """Test successful negotiation for round 1."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 1,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 1100.0  # 1000 + (1300-1000)/3
        assert data["attempt_number"] == 2
        assert data["message"] == "Counter-offer for round 1"

    def test_successful_negotiation_round_2(
        self, client: TestClient, valid_headers: dict
    ):
        """Test successful negotiation for round 2."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 2,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 1100.0
        assert data["attempt_number"] == 3
        assert data["message"] == "Counter-offer for round 2"

    def test_final_negotiation_round(self, client: TestClient, valid_headers: dict):
        """Test final negotiation round (round 3)."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 3,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 1100.0
        assert data["attempt_number"] == 3  # Capped at 3
        assert data["message"] == "Final offer - no further negotiation available"

    def test_negotiation_with_same_offers(
        self, client: TestClient, valid_headers: dict
    ):
        """Test negotiation when initial and customer offers are the same."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1000.0,
                "attempt_number": 1,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 1000.0  # No change when offers are equal
        assert data["attempt_number"] == 2
        assert data["message"] == "Counter-offer for round 1"

    def test_negotiation_with_negative_values(
        self, client: TestClient, valid_headers: dict
    ):
        """Test negotiation with negative values."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": -100.0,
                "customer_offer": 200.0,
                "attempt_number": 1,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 0.0  # -100 + (200-(-100))/3 = 0
        assert data["attempt_number"] == 2

    def test_negotiation_with_customer_offer_lower_than_initial(
        self, client: TestClient, valid_headers: dict
    ):
        """Test negotiation when customer offer is lower than initial."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 800.0,
                "attempt_number": 1,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 933.33  # 1000 + (800-1000)/3
        assert data["attempt_number"] == 2

    def test_invalid_attempt_number_too_high(
        self, client: TestClient, valid_headers: dict
    ):
        """Test validation error for attempt number > 3."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 4,
            },
            headers=valid_headers,
        )

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        assert any(
            "less than or equal to 3" in str(detail) for detail in error["detail"]
        )

    def test_invalid_attempt_number_too_low(
        self, client: TestClient, valid_headers: dict
    ):
        """Test validation error for attempt number < 1."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 0,
            },
            headers=valid_headers,
        )

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        assert any(
            "greater than or equal to 1" in str(detail) for detail in error["detail"]
        )

    def test_missing_parameters(self, client: TestClient, valid_headers: dict):
        """Test validation error for missing parameters."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0
            },  # Missing customer_offer and attempt_number
            headers=valid_headers,
        )

        assert response.status_code == 422

    def test_unauthorized_without_api_key(self, client: TestClient):
        """Test unauthorized access without API key."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 1,
            },
        )

        assert response.status_code == 401

    def test_unauthorized_with_invalid_api_key(self, client: TestClient):
        """Test unauthorized access with invalid API key."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 1,
            },
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401

    def test_rounding_behavior(self, client: TestClient, valid_headers: dict):
        """Test that offers are properly rounded to 2 decimal places."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1301.0,
                "attempt_number": 1,
            },
            headers=valid_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # 1000 + (1301-1000)/3 = 1000 + 100.33 = 1100.33
        assert data["new_offer"] == 1100.33
        assert isinstance(data["new_offer"], float)

    def test_alternative_api_key_header(self, client: TestClient):
        """Test API key via Authorization header."""
        response = client.get(
            "/api/v1/negotiations",
            params={
                "initial_offer": 1000.0,
                "customer_offer": 1300.0,
                "attempt_number": 1,
            },
            headers={"Authorization": "ApiKey dev-local-api-key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_offer"] == 1100.0
