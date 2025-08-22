"""Unit tests for domain entities."""

import uuid
from datetime import datetime, timezone

from src.core.domain.entities import Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import EquipmentType, Location, Rate


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
            miles="716",
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
        assert load.miles == "716"
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
            miles="500",
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
