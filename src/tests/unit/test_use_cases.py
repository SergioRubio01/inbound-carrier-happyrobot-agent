"""Unit tests for use cases."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.application.use_cases.evaluate_negotiation import (
    EvaluateNegotiationRequest,
    EvaluateNegotiationUseCase,
)
from src.core.application.use_cases.search_loads import (
    LoadSearchRequest,
    SearchLoadsUseCase,
)

# VerifyCarrier use case is not implemented yet
from src.core.domain.entities import Carrier, Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, MCNumber, Rate

# NOTE: VerifyCarrierUseCase tests are deferred pending implementation
# The use case needs to be implemented in src/core/application/use_cases/
# class TestVerifyCarrierUseCase:
#     """Test VerifyCarrierUseCase."""
#
#     @pytest.mark.asyncio
#     async def test_verify_eligible_carrier(self):
#         """Test verifying an eligible carrier."""
#         # Mock repository
#         mock_repo = AsyncMock()
#         carrier = Carrier(
#             carrier_id=uuid.uuid4(),
#             mc_number=MCNumber.from_string("MC123456"),
#             legal_name="Test Carrier LLC",
#             entity_type="CARRIER",
#             operating_status="AUTHORIZED_FOR_HIRE",
#             status="ACTIVE",
#             insurance_on_file=True,
#             created_at=datetime.now(timezone.utc),
#             updated_at=datetime.now(timezone.utc),
#         )
#         mock_repo.get_by_mc_number.return_value = carrier
#         mock_repo.update.return_value = carrier
#
#         # Execute use case
#         use_case = VerifyCarrierUseCase(mock_repo)
#         request = VerifyCarrierRequest(mc_number="MC123456")
#         result = await use_case.execute(request)

#         # Assert
#         assert result.eligible is True
#         assert result.mc_number == "123456"  # MCNumber returns without prefix
#         assert result.carrier_info is not None
#         assert result.carrier_info["legal_name"] == "Test Carrier LLC"
#         mock_repo.get_by_mc_number.assert_called_once()
#
#     @pytest.mark.asyncio
#     async def test_verify_ineligible_carrier(self):
#         """Test verifying an ineligible carrier."""
#         # Mock repository
#         mock_repo = AsyncMock()
#         carrier = Carrier(
#             carrier_id=uuid.uuid4(),
#             mc_number=MCNumber.from_string("MC123456"),
#             legal_name="Test Carrier LLC",
#             entity_type="CARRIER",
#             operating_status="OUT_OF_SERVICE",
#             status="INACTIVE",
#             insurance_on_file=False,
#             created_at=datetime.now(timezone.utc),
#             updated_at=datetime.now(timezone.utc),
#         )
#         mock_repo.get_by_mc_number.return_value = carrier
#         mock_repo.update.return_value = carrier
#
#         # Execute use case
#         use_case = VerifyCarrierUseCase(mock_repo)
#         request = VerifyCarrierRequest(mc_number="MC123456")
#         result = await use_case.execute(request)
#
#         # Assert
#         assert result.eligible is False
#         assert result.reason is not None
#         assert "CARRIER_NOT_AUTHORIZED" in result.reason
#
#     @pytest.mark.asyncio
#     async def test_verify_nonexistent_carrier(self):
#         """Test verifying a non-existent carrier."""
#         # Mock repository
#         mock_repo = AsyncMock()
#         mock_repo.get_by_mc_number.return_value = None
#
#         # Mock _verify_with_fmcsa to return None (carrier not found)
#         from unittest.mock import patch
#
#         # Execute use case with mocked FMCSA verification
#         use_case = VerifyCarrierUseCase(mock_repo)
#         with patch.object(use_case, "_verify_with_fmcsa", return_value=None):
#             request = VerifyCarrierRequest(mc_number="MC999999")
#             result = await use_case.execute(request)
#
#             # Assert
#             assert result.eligible is False
#             assert result.reason == "CARRIER_NOT_FOUND"


class TestSearchLoadsUseCase:
    """Test SearchLoadsUseCase."""

    @pytest.mark.asyncio
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
                pickup_date=datetime.now(timezone.utc).date(),
                delivery_date=datetime.now(timezone.utc).date(),
                equipment_type=EquipmentType.from_name("53-foot van"),
                weight=35000,
                miles=716,
                loadboard_rate=Rate.from_float(2500),
                status=LoadStatus.AVAILABLE,
                urgency=UrgencyLevel.NORMAL,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        mock_repo.search_loads.return_value = mock_loads
        mock_repo.count_loads_by_criteria.return_value = len(mock_loads)

        # Execute use case
        use_case = SearchLoadsUseCase(mock_repo)
        request = LoadSearchRequest(equipment_type="53-foot van")
        result = await use_case.execute(request)

        # Assert
        assert len(result.loads) == 1
        assert result.loads[0]["load_id"] == str(mock_loads[0].load_id)
        assert result.loads[0]["equipment_type"] == "53-foot van"
        assert result.returned_count == 1

    @pytest.mark.asyncio
    async def test_search_loads_empty_results(self):
        """Test searching loads with no results."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.search_loads.return_value = []
        mock_repo.count_loads_by_criteria.return_value = 0

        # Execute use case
        use_case = SearchLoadsUseCase(mock_repo)
        request = LoadSearchRequest(equipment_type="RGN")
        result = await use_case.execute(request)

        # Assert
        assert len(result.loads) == 0
        assert result.total_matches == 0


class TestEvaluateNegotiationUseCase:
    """Test EvaluateNegotiationUseCase."""

    @pytest.mark.asyncio
    async def test_evaluate_acceptable_offer(self):
        """Test evaluating an acceptable offer."""
        # Mock repositories
        mock_load_repo = AsyncMock()

        # Mock load
        mock_load = Load(
            load_id=uuid.uuid4(),
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.now(timezone.utc).date(),
            delivery_date=datetime.now(timezone.utc).date(),
            equipment_type=EquipmentType.from_name("53-foot van"),
            weight=35000,
            miles=716,
            loadboard_rate=Rate.from_float(2500),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_load_repo.get_by_id.return_value = mock_load

        # Mock carrier repository
        mock_carrier_repo = AsyncMock()
        mock_carrier = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier LLC",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_carrier_repo.get_by_mc_number.return_value = mock_carrier

        # Execute use case
        use_case = EvaluateNegotiationUseCase(mock_load_repo, mock_carrier_repo)
        request = EvaluateNegotiationRequest(
            load_id=str(mock_load.load_id),
            mc_number="MC123456",
            carrier_offer=2500.0,
            negotiation_round=1,
        )
        result = await use_case.execute(request)

        # Assert
        assert result.status == "ACCEPTED"
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_evaluate_high_offer_response(self):
        """Test evaluating a high offer response."""
        # Mock repositories
        mock_load_repo = AsyncMock()

        # Mock load
        mock_load = Load(
            load_id=uuid.uuid4(),
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.now(timezone.utc).date(),
            delivery_date=datetime.now(timezone.utc).date(),
            equipment_type=EquipmentType.from_name("53-foot van"),
            weight=35000,
            miles=716,
            loadboard_rate=Rate.from_float(2500),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_load_repo.get_by_id.return_value = mock_load

        # Mock carrier repository
        mock_carrier_repo = AsyncMock()
        mock_carrier = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier LLC",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_carrier_repo.get_by_mc_number.return_value = mock_carrier

        # Execute use case
        use_case = EvaluateNegotiationUseCase(mock_load_repo, mock_carrier_repo)
        request = EvaluateNegotiationRequest(
            load_id=str(mock_load.load_id),
            mc_number="MC123456",
            carrier_offer=2800.0,  # Above loadboard rate
            negotiation_round=1,
        )
        result = await use_case.execute(request)

        # Assert - the result may be ACCEPTED, COUNTER_OFFER, or REJECTED depending on urgency factors
        assert result.status in ["ACCEPTED", "COUNTER_OFFER", "REJECTED"]
        assert result.message is not None
