"""
File: equipment_type.py
Description: Equipment type value object
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..exceptions.base import DomainException


class InvalidEquipmentTypeException(DomainException):
    """Exception raised when equipment type is invalid."""
    pass


class EquipmentCategory(Enum):
    """Equipment categories."""
    VAN = "VAN"
    FLATBED = "FLATBED"
    SPECIALIZED = "SPECIALIZED"
    POWER_ONLY = "POWER_ONLY"


@dataclass(frozen=True)
class EquipmentType:
    """Value object for equipment type."""

    name: str
    category: Optional[EquipmentCategory] = None
    typical_capacity: Optional[int] = None  # in pounds
    requires_cdl: bool = True

    # Standard equipment types
    STANDARD_TYPES = {
        "53-foot van": {"category": EquipmentCategory.VAN, "capacity": 45000},
        "48-foot van": {"category": EquipmentCategory.VAN, "capacity": 43000},
        "Reefer": {"category": EquipmentCategory.VAN, "capacity": 43000},
        "Flatbed": {"category": EquipmentCategory.FLATBED, "capacity": 48000},
        "Step Deck": {"category": EquipmentCategory.FLATBED, "capacity": 48000},
        "Double Drop": {"category": EquipmentCategory.FLATBED, "capacity": 45000},
        "RGN": {"category": EquipmentCategory.SPECIALIZED, "capacity": 70000},
        "Power Only": {"category": EquipmentCategory.POWER_ONLY, "capacity": None},
        "Hotshot": {"category": EquipmentCategory.SPECIALIZED, "capacity": 20000},
        "Box Truck": {"category": EquipmentCategory.VAN, "capacity": 12000, "cdl": False},
    }

    def __post_init__(self):
        """Validate and normalize equipment type."""
        if not self.name or not self.name.strip():
            raise InvalidEquipmentTypeException("Equipment type name cannot be empty")

        # Normalize name
        normalized_name = self.name.strip()
        object.__setattr__(self, 'name', normalized_name)

        # Set standard properties if this is a known type
        if normalized_name in self.STANDARD_TYPES:
            standard = self.STANDARD_TYPES[normalized_name]

            if self.category is None:
                object.__setattr__(self, 'category', standard["category"])

            if self.typical_capacity is None:
                object.__setattr__(self, 'typical_capacity', standard["capacity"])

            if "cdl" in standard:
                object.__setattr__(self, 'requires_cdl', standard["cdl"])

    @classmethod
    def from_name(cls, name: str) -> 'EquipmentType':
        """Create EquipmentType from name string."""
        return cls(name=name)

    @property
    def is_van_type(self) -> bool:
        """Check if this is a van-type equipment."""
        return self.category == EquipmentCategory.VAN

    @property
    def is_flatbed_type(self) -> bool:
        """Check if this is a flatbed-type equipment."""
        return self.category == EquipmentCategory.FLATBED

    @property
    def is_specialized(self) -> bool:
        """Check if this is specialized equipment."""
        return self.category == EquipmentCategory.SPECIALIZED

    def can_haul_weight(self, weight: int) -> bool:
        """Check if this equipment can haul the given weight."""
        if self.typical_capacity is None:
            return True  # Unknown capacity, assume it can handle it
        return weight <= self.typical_capacity

    def __str__(self) -> str:
        return self.name
