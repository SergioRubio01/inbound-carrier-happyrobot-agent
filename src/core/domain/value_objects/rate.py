"""
File: rate.py
Description: Rate value object for pricing
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Union

from ..exceptions.base import DomainException


class InvalidRateException(DomainException):
    """Exception raised when rate is invalid."""

    pass


@dataclass(frozen=True)
class Rate:
    """Value object for monetary rates."""

    amount: Decimal

    def __post_init__(self):
        """Validate rate after initialization."""
        if self.amount < 0:
            raise InvalidRateException("Rate cannot be negative")

        if self.amount > Decimal("999999.99"):
            raise InvalidRateException("Rate cannot exceed $999,999.99")

        # Ensure amount is rounded to 2 decimal places
        rounded_amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", rounded_amount)

    @classmethod
    def from_float(cls, value: Union[float, int, str]) -> "Rate":
        """Create Rate from float, int, or string."""
        return cls(amount=Decimal(str(value)))

    def add(self, other: "Rate") -> "Rate":
        """Add two rates together."""
        return Rate(amount=self.amount + other.amount)

    def subtract(self, other: "Rate") -> "Rate":
        """Subtract one rate from another."""
        return Rate(amount=self.amount - other.amount)

    def multiply(self, factor: Union[float, int, Decimal]) -> "Rate":
        """Multiply rate by a factor."""
        return Rate(amount=self.amount * Decimal(str(factor)))

    def divide(self, divisor: Union[float, int, Decimal]) -> "Rate":
        """Divide rate by a divisor."""
        if divisor == 0:
            raise InvalidRateException("Cannot divide by zero")
        return Rate(amount=self.amount / Decimal(str(divisor)))

    def percentage_difference(self, other: "Rate") -> Decimal:
        """Calculate percentage difference between two rates."""
        if other.amount == 0:
            return Decimal("0")
        return ((self.amount - other.amount) / other.amount) * 100

    def to_float(self) -> float:
        """Convert to float for external APIs."""
        return float(self.amount)

    def __str__(self) -> str:
        return f"${self.amount:.2f}"

    def __lt__(self, other: "Rate") -> bool:
        return self.amount < other.amount

    def __le__(self, other: "Rate") -> bool:
        return self.amount <= other.amount

    def __gt__(self, other: "Rate") -> bool:
        return self.amount > other.amount

    def __ge__(self, other: "Rate") -> bool:
        return self.amount >= other.amount
