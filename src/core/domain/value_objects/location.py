"""
File: location.py
Description: Location value object
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from typing import Optional

from ..exceptions.base import DomainException


class InvalidLocationException(DomainException):
    """Exception raised when location is invalid."""
    pass


@dataclass(frozen=True)
class Location:
    """Value object for geographic location."""

    city: str
    state: str
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self):
        """Validate location after initialization."""
        if not self.city or not self.city.strip():
            raise InvalidLocationException("City cannot be empty")

        if not self.state or len(self.state) != 2:
            raise InvalidLocationException("State must be a 2-letter code")

        # Normalize state to uppercase
        object.__setattr__(self, 'state', self.state.upper())

        # Validate coordinates if provided
        if self.latitude is not None:
            if not (-90 <= self.latitude <= 90):
                raise InvalidLocationException("Latitude must be between -90 and 90")

        if self.longitude is not None:
            if not (-180 <= self.longitude <= 180):
                raise InvalidLocationException("Longitude must be between -180 and 180")

    @property
    def display_name(self) -> str:
        """Get display name for the location."""
        if self.zip_code:
            return f"{self.city}, {self.state} {self.zip_code}"
        return f"{self.city}, {self.state}"

    @property
    def state_lane_key(self) -> str:
        """Get state lane key for rate history."""
        return self.state

    def distance_to(self, other: 'Location') -> Optional[float]:
        """Calculate distance to another location (requires coordinates)."""
        if (self.latitude is None or self.longitude is None or
            other.latitude is None or other.longitude is None):
            return None

        # Haversine formula
        import math

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in miles
        r = 3956

        return c * r

    def __str__(self) -> str:
        return self.display_name
