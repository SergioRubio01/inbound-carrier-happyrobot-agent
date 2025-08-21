"""Unit tests for domain entities."""

import uuid
from datetime import datetime, timezone

from src.core.domain.entities import Carrier, Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, MCNumber, Rate


class TestCarrier:
    """Test Carrier entity."""

    def test_carrier_creation(self):
        """Test creating a carrier entity."""
        carrier = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            dot_number="DOT789012",
            legal_name="Test Carrier LLC",
            dba_name="Test Carrier",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert carrier.mc_number == MCNumber.from_string("MC123456")
        assert carrier.legal_name == "Test Carrier LLC"
        assert carrier.is_eligible

    def test_carrier_eligibility(self):
        """Test carrier eligibility logic."""
        # Eligible carrier
        eligible_carrier = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert eligible_carrier.is_eligible

        # Ineligible carrier (no insurance)
        ineligible_carrier = Carrier(
            carrier_id=uuid.uuid4(),
            mc_number=MCNumber.from_string("MC123456"),
            legal_name="Test Carrier",
            entity_type="CARRIER",
            operating_status="AUTHORIZED_FOR_HIRE",
            status="ACTIVE",
            insurance_on_file=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert not ineligible_carrier.is_eligible


class TestLoad:
    """Test Load entity."""

    def test_load_creation(self):
        """Test creating a load entity."""
        load = Load(
            load_id=uuid.uuid4(),
            reference_number="LOAD001",
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.now(timezone.utc).date(),
            delivery_date=datetime.now(timezone.utc).date(),
            equipment_type=EquipmentType.from_name("DRY_VAN"),
            weight=35000,
            miles=716,
            loadboard_rate=Rate.from_float(2500),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert load.reference_number == "LOAD001"
        assert load.origin is not None and load.origin.city == "Chicago"
        assert load.destination is not None and load.destination.city == "Atlanta"
        assert load.miles == 716
        assert (
            load.loadboard_rate is not None and load.loadboard_rate.to_float() == 2500
        )

    def test_load_rate_per_mile(self):
        """Test load rate per mile calculation."""
        load = Load(
            load_id=uuid.uuid4(),
            origin=Location("Chicago", "IL", "60601"),
            destination=Location("Atlanta", "GA", "30301"),
            pickup_date=datetime.now(timezone.utc).date(),
            delivery_date=datetime.now(timezone.utc).date(),
            equipment_type=EquipmentType.from_name("DRY_VAN"),
            weight=35000,
            miles=500,
            loadboard_rate=Rate.from_float(2000),
            status=LoadStatus.AVAILABLE,
            urgency=UrgencyLevel.NORMAL,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        rate_per_mile = load.rate_per_mile
        assert rate_per_mile is not None
        assert rate_per_mile.to_float() == 4.0  # $2000 / 500 miles
