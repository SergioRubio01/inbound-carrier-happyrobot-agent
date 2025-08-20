"""Unit tests for value objects."""

import pytest

from src.core.domain.value_objects import EquipmentType, Location, MCNumber, Rate


class TestMCNumber:
    """Test MCNumber value object."""

    def test_valid_mc_number(self):
        """Test creating a valid MC number."""
        mc = MCNumber.from_string("MC123456")
        assert mc.value == "123456"
        assert str(mc) == "MC123456"

    def test_mc_number_without_prefix(self):
        """Test creating MC number without prefix."""
        mc = MCNumber.from_string("123456")
        assert mc.value == "123456"
        assert str(mc) == "MC123456"

    def test_invalid_mc_number(self):
        """Test invalid MC number raises error."""
        with pytest.raises(ValueError):
            MCNumber.from_string("invalid")

    def test_mc_number_equality(self):
        """Test MC number equality."""
        mc1 = MCNumber.from_string("MC123456")
        mc2 = MCNumber.from_string("123456")
        assert mc1 == mc2


class TestRate:
    """Test Rate value object."""

    def test_rate_from_float(self):
        """Test creating rate from float."""
        rate = Rate.from_float(1500.50)
        assert rate.to_float() == 1500.50
        assert str(rate) == "$1,500.50"

    def test_rate_from_cents(self):
        """Test creating rate from cents."""
        rate = Rate(150050)  # $1500.50 in cents
        assert rate.to_float() == 1500.50
        assert rate.cents == 150050

    def test_rate_comparison(self):
        """Test rate comparison."""
        rate1 = Rate.from_float(1000)
        rate2 = Rate.from_float(1500)
        assert rate1 < rate2
        assert rate2 > rate1
        assert rate1 != rate2

    def test_rate_arithmetic(self):
        """Test rate arithmetic operations."""
        rate1 = Rate.from_float(1000)
        rate2 = Rate.from_float(500)

        # Addition
        result = rate1 + rate2
        assert result.to_float() == 1500

        # Subtraction
        result = rate1 - rate2
        assert result.to_float() == 500

        # Multiplication
        result = rate1 * 1.1
        assert result.to_float() == 1100

        # Division
        result = rate1 / 2
        assert result.to_float() == 500


class TestLocation:
    """Test Location value object."""

    def test_location_creation(self):
        """Test creating a location."""
        location = Location(city="Chicago", state="IL", zip_code="60601")
        assert location.city == "Chicago"
        assert location.state == "IL"
        assert location.zip_code == "60601"

    def test_location_string_representation(self):
        """Test location string representation."""
        location = Location(city="Chicago", state="IL", zip_code="60601")
        assert str(location) == "Chicago, IL 60601"

    def test_location_without_zip(self):
        """Test location without zip code."""
        location = Location(city="Chicago", state="IL", zip_code=None)
        assert str(location) == "Chicago, IL"


class TestEquipmentType:
    """Test EquipmentType value object."""

    @pytest.mark.unit
    def test_equipment_type_creation(self):
        """Test creating equipment type."""
        eq = EquipmentType.from_name("DRY_VAN")
        assert eq.name == "DRY_VAN"
        assert eq.description == "Dry Van"

    def test_all_equipment_types(self):
        """Test all equipment types are accessible."""
        types = EquipmentType.all_types()
        assert len(types) > 0
        assert any(t.name == "DRY_VAN" for t in types)
        assert any(t.name == "REEFER" for t in types)
        assert any(t.name == "FLATBED" for t in types)

    def test_invalid_equipment_type(self):
        """Test invalid equipment type raises error."""
        with pytest.raises(ValueError):
            EquipmentType.from_name("INVALID_TYPE")
