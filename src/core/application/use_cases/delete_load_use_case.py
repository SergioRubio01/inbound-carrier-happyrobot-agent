"""
File: delete_load_use_case.py
Description: Use case for deleting loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from src.core.domain.entities import Load, LoadStatus
from src.core.ports.repositories import ILoadRepository
from src.core.domain.exceptions.base import DomainException


class LoadNotFoundException(DomainException):
    """Exception raised when load is not found."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class LoadDeletionException(DomainException):
    """Exception raised when load deletion fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class DeleteLoadRequest:
    """Request for deleting a load."""
    load_id: UUID


@dataclass
class DeleteLoadResponse:
    """Response for load deletion."""
    load_id: str
    reference_number: str
    deleted_at: datetime


class DeleteLoadUseCase:
    """Use case for deleting loads."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: DeleteLoadRequest) -> DeleteLoadResponse:
        """Execute load deletion."""
        try:
            # Get the load by ID
            load = await self.load_repository.get_by_id(request.load_id)
            if not load:
                raise LoadNotFoundException(f"Load with ID {request.load_id} not found")

            # Validate business rules
            await self._validate_deletion_rules(load)

            # Perform soft delete
            success = await self.load_repository.delete(request.load_id)
            if not success:
                raise LoadDeletionException(f"Failed to delete load {request.load_id}")

            return DeleteLoadResponse(
                load_id=str(load.load_id),
                reference_number=load.reference_number,
                deleted_at=datetime.utcnow()
            )

        except LoadNotFoundException:
            raise
        except LoadDeletionException:
            raise
        except Exception as e:
            raise LoadDeletionException(f"Failed to delete load: {str(e)}")

    async def _validate_deletion_rules(self, load: Load) -> None:
        """Validate business rules for load deletion."""
        # Cannot delete loads that are in transit or delivered
        if load.status == LoadStatus.IN_TRANSIT:
            raise LoadDeletionException(f"Cannot delete load {load.reference_number} - load is in transit")

        if load.status == LoadStatus.DELIVERED:
            raise LoadDeletionException(f"Cannot delete load {load.reference_number} - load has been delivered")
