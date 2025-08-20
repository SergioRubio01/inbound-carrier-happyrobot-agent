"""
File: mc_number.py
Description: Motor Carrier number value object
Author: HappyRobot Team
Created: 2024-08-14
"""

import re
from dataclasses import dataclass
from typing import Union

from ..exceptions.base import DomainException


class InvalidMCNumberException(DomainException):
    """Exception raised when MC number is invalid."""

    pass


@dataclass(frozen=True)
class MCNumber:
    """Value object for Motor Carrier number."""

    value: str

    def __post_init__(self):
        """Validate MC number after initialization."""
        if not self.value:
            raise InvalidMCNumberException("MC number cannot be empty")

        # Remove any non-digit characters for validation
        digits_only = re.sub(r"\D", "", self.value)

        if not digits_only:
            raise InvalidMCNumberException("MC number must contain digits")

        if len(digits_only) < 6 or len(digits_only) > 8:
            raise InvalidMCNumberException("MC number must be 6-8 digits")

        # Store the normalized value (digits only)
        object.__setattr__(self, "value", digits_only)

    @classmethod
    def from_string(cls, value: Union[str, int]) -> "MCNumber":
        """Create MCNumber from string or integer."""
        if isinstance(value, int):
            value = str(value)
        return cls(value=value)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, MCNumber):
            return self.value == other.value
        return False
