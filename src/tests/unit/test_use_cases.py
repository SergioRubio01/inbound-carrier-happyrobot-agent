"""Unit tests for use cases."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.core.application.use_cases.evaluate_negotiation import (
    EvaluateNegotiationUseCase,
)
from src.core.application.use_cases.search_loads import SearchLoadsUseCase
from src.core.application.use_cases.verify_carrier import VerifyCarrierUseCase
from src.core.domain.entities import Carrier, Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, MCNumber, Rate


@pytest.mark.asyncio
class TestVerifyCarrierUseCase:
    """Test VerifyCarrierUseCase."""

    async def test_verify_eligible_carrier(self):
        """Test verifying an eligible carrier."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_by_mc_number.return_value = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier LLC",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Execute use case
        use_case = VerifyCarrierUseCase(mock_repo)
        result = await use_case.execute("MC123456")

        # Assert
        assert result["eligible"] is True
        assert result["mc_number"] == "MC123456"
        assert result["legal_name"] == "Test Carrier LLC"
        mock_repo.get_by_mc_number.assert_called_once()

    async def test_verify_ineligible_carrier(self):
        """Test verifying an ineligible carrier."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_by_mc_number.return_value = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier LLC",
            entity_type="CARRIER",
            operating_status="OUT_OF_SERVICE",
            status="INACTIVE",
            insurance_on_file=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Execute use case
        use_case = VerifyCarrierUseCase(mock_repo)
        result = await use_case.execute("MC123456")

        # Assert
        assert result["eligible"] is False
        assert "OUT_OF_SERVICE" in result["reason"]

    async def test_verify_nonexistent_carrier(self):
        """Test verifying a non-existent carrier."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_by_mc_number.return_value = None

        # Execute use case
        use_case = VerifyCarrierUseCase(mock_repo)
        result = await use_case.execute("MC999999")

        # Assert
        assert result["eligible"] is False
        assert "not found" in result["reason"]


@pytest.mark.asyncio
class TestSearchLoadsUseCase:
    """Test SearchLoadsUseCase."""

    async def test_search_loads_with_equipment_filter(self):
        """Test searching loads with equipment type filter."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_loads = [
            Load(
                load_id=uuid.uuid4(),
                reference_number="LOAD001",
                origin=Location("Chicago", "IL", "60601"),
                destination=Location("Atlanta", "GA", "30301"),
                pickup_date=datetime.utcnow().date(),
                delivery_date=datetime.utcnow().date(),
                equipment_type=EquipmentType.from_name("DRY_VAN"),
                weight=35000,
                miles=716,
                loadboard_rate=Rate.from_float(2500),
                status=LoadStatus.AVAILABLE,
                urgency=UrgencyLevel.NORMAL,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        ]
        mock_repo.search_loads.return_value = mock_loads

        # Execute use case
        use_case = SearchLoadsUseCase(mock_repo)
        result = await use_case.execute(equipment_type="DRY_VAN")

        # Assert
        assert len(result["loads"]) == 1
        assert result["loads"][0]["reference_number"] == "LOAD001"
        assert result["loads"][0]["equipment_type"] == "DRY_VAN"
        assert result["total_count"] == 1

    async def test_search_loads_empty_results(self):
        """Test searching loads with no results."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.search_loads.return_value = []

        # Execute use case
        use_case = SearchLoadsUseCase(mock_repo)
        result = await use_case.execute(equipment_type="SPECIALIZED")

        # Assert
        assert len(result["loads"]) == 0
        assert result["total_count"] == 0


@pytest.mark.asyncio
class TestEvaluateNegotiationUseCase:
    """Test EvaluateNegotiationUseCase."""

    async def test_evaluate_acceptable_offer(self):
        """Test evaluating an acceptable offer."""
        # Mock repositories
        mock_negotiation_repo = AsyncMock()
        mock_load_repo = AsyncMock()

        # Mock load
        mock_load = Load(
            load_id=uuid.uuid4(),
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.utcnow().date(),
            delivery_date=datetime.utcnow().date(),
            equipment_type=EquipmentType.from_name("DRY_VAN"),
            weight=35000,
            miles=716,
            loadboard_rate=Rate.from_float(2500),
            minimum_rate=Rate.from_float(2400),
            target_rate=Rate.from_float(2500),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_load_repo.get_by_id.return_value = mock_load

        # Execute use case
        use_case = EvaluateNegotiationUseCase(mock_negotiation_repo, mock_load_repo)
        result = await use_case.execute(
            session_id="session123",
            load_id=str(mock_load.load_id),
            carrier_offer=2500.0,
            round_number=1,
        )

        # Assert
        assert result["response"] == "ACCEPTED"
        assert result["message"] is not None

    async def test_evaluate_high_offer_counter(self):
        """Test evaluating a high offer that triggers counter-offer."""
        # Mock repositories
        mock_negotiation_repo = AsyncMock()
        mock_load_repo = AsyncMock()

        # Mock load
        mock_load = Load(
            load_id=uuid.uuid4(),
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.utcnow().date(),
            delivery_date=datetime.utcnow().date(),
            equipment_type=EquipmentType.from_name("DRY_VAN"),
            weight=35000,
            miles=716,
            loadboard_rate=Rate.from_float(2500),
            minimum_rate=Rate.from_float(2400),
            maximum_rate=Rate.from_float(2600),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_load_repo.get_by_id.return_value = mock_load

        # Execute use case
        use_case = EvaluateNegotiationUseCase(mock_negotiation_repo, mock_load_repo)
        result = await use_case.execute(
            session_id="session123",
            load_id=str(mock_load.load_id),
            carrier_offer=2800.0,  # Above maximum
            round_number=1,
        )

        # Assert
        assert result["response"] == "COUNTER_OFFER"
        assert result["counter_offer"] is not None
        assert result["counter_offer"] <= 2600  # Should not exceed maximum
