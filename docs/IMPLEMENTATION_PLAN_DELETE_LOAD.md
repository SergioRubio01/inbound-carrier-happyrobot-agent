# DELETE Load Endpoint Implementation Plan

## Executive Summary

This document outlines the implementation plan for adding a DELETE endpoint to the HappyRobot FDE platform's load management system. The endpoint will allow authorized users to remove load records from the database following the hexagonal architecture pattern established in the codebase. The implementation will ensure data integrity through proper cascade handling and maintain consistency with existing patterns.

## Business Objectives

- Enable removal of incorrect, duplicate, or obsolete load records
- Maintain data integrity with related tables (calls, negotiations)
- Provide proper error handling and validation
- Ensure secure access through API key authentication
- Support soft deletion to preserve historical data

## Technical Architecture Overview

The implementation follows the hexagonal architecture:
- **API Layer**: FastAPI endpoint in `src/interfaces/api/v1/loads.py`
- **Application Layer**: DeleteLoadUseCase in `src/core/application/use_cases/`
- **Domain Layer**: Load entity and exceptions
- **Infrastructure Layer**: PostgresLoadRepository with soft delete
- **Testing**: Unit and integration tests

## Detailed Implementation Tasks

### Task 1: Create DeleteLoadUseCase
**Agent**: backend-agent
**Priority**: High
**Dependencies**: None

**File to Create**: `src/core/application/use_cases/delete_load_use_case.py`

```python
"""
File: delete_load_use_case.py
Description: Use case for deleting loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from src.core.ports.repositories import ILoadRepository
from src.core.domain.exceptions.base import DomainException


class LoadNotFoundException(DomainException):
    """Exception raised when load is not found."""

    def __init__(self, load_id: UUID):
        self.load_id = load_id
        super().__init__(f"Load with ID '{load_id}' not found")


class LoadDeletionException(DomainException):
    """Exception raised when load deletion fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class DeleteLoadRequest:
    """Request for deleting a load."""
    load_id: UUID
    soft_delete: bool = True  # Default to soft delete
    deleted_by: str = "API"  # Track who deleted


@dataclass
class DeleteLoadResponse:
    """Response for load deletion."""
    load_id: str
    deleted: bool
    deletion_type: str  # "soft" or "hard"
    deleted_at: datetime


class DeleteLoadUseCase:
    """Use case for deleting loads."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: DeleteLoadRequest) -> DeleteLoadResponse:
        """Execute load deletion."""
        try:
            # Check if load exists
            load = await self.load_repository.get_by_id(request.load_id)
            if not load:
                raise LoadNotFoundException(request.load_id)

            # Check if load can be deleted
            await self._validate_deletion(load)

            # Perform deletion
            deleted = await self.load_repository.delete(request.load_id)

            if not deleted:
                raise LoadDeletionException(f"Failed to delete load '{request.load_id}'")

            return DeleteLoadResponse(
                load_id=str(request.load_id),
                deleted=True,
                deletion_type="soft" if request.soft_delete else "hard",
                deleted_at=datetime.utcnow()
            )

        except LoadNotFoundException:
            raise
        except Exception as e:
            raise LoadDeletionException(f"Failed to delete load: {str(e)}")

    async def _validate_deletion(self, load) -> None:
        """Validate if load can be deleted."""
        # Business rules for deletion
        if load.status.value == 'IN_TRANSIT':
            raise LoadDeletionException("Cannot delete load that is in transit")

        if load.status.value == 'DELIVERED':
            raise LoadDeletionException("Cannot delete delivered loads")

        # Add more business rules as needed
```

**Tests Required**:
- Test successful deletion
- Test load not found scenario
- Test deletion validation rules
- Test soft delete behavior

---

### Task 2: Update PostgresLoadRepository Delete Method
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Task 1

**File to Modify**: `src/infrastructure/database/postgres/load_repository.py`

The existing `delete` method (lines 192-204) already implements soft delete. We need to ensure it's working correctly and add any necessary enhancements:

**Current Implementation Review**:
- Already implements soft delete
- Sets `deleted_at` timestamp
- Sets `is_active = False`
- Returns boolean success

**Potential Enhancement**:
```python
async def delete(self, load_id: UUID) -> bool:
    """Delete load (soft delete)."""
    stmt = select(LoadModel).where(LoadModel.load_id == load_id)
    result = await self.session.execute(stmt)
    model = result.scalar_one_or_none()

    if model:
        # Check if already deleted
        if model.deleted_at is not None:
            return False  # Already deleted

        model.deleted_at = datetime.utcnow()
        model.is_active = False
        model.updated_at = datetime.utcnow()
        model.status = 'CANCELLED'  # Update status to cancelled
        await self.session.flush()
        return True
    return False
```

---

### Task 3: Add DELETE Endpoint to Loads API
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Tasks 1, 2

**File to Modify**: `src/interfaces/api/v1/loads.py`

**Location**: Add after the GET endpoint (after line 270)

```python
@router.delete("/{load_id}", status_code=204)
async def delete_load(
    load_id: str,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Delete a load from the system.

    Performs a soft delete by marking the load as deleted rather than
    removing it from the database. This preserves historical data and
    maintains referential integrity with related records.

    Path Parameters:
        load_id: The UUID of the load to delete

    Returns:
        204 No Content on successful deletion

    Raises:
        HTTPException:
            - 400 for invalid UUID format
            - 404 if load not found
            - 409 if load cannot be deleted due to business rules
            - 500 for internal server errors
    """
    try:
        # Validate UUID format
        from uuid import UUID as uuid_validator
        try:
            load_uuid = uuid_validator(load_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid load ID format: {load_id}")

        # Initialize repository and use case
        load_repo = PostgresLoadRepository(session)
        use_case = DeleteLoadUseCase(load_repo)

        # Import the request class
        from src.core.application.use_cases.delete_load_use_case import DeleteLoadRequest

        # Create use case request
        use_case_request = DeleteLoadRequest(
            load_id=load_uuid,
            soft_delete=True,
            deleted_by="API"
        )

        # Execute use case
        response = await use_case.execute(use_case_request)

        # Commit the transaction
        await session.commit()

        # Return 204 No Content on success
        return None

    except Exception as e:
        # Rollback on error
        await session.rollback()

        error_msg = str(e)

        # Handle specific exceptions
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "cannot delete" in error_msg.lower() or "in transit" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        elif "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")
```

**Import Additions** (at top of file):
```python
from src.core.application.use_cases.delete_load_use_case import DeleteLoadUseCase
```

---

### Task 4: Create Unit Tests for DeleteLoadUseCase
**Agent**: qa-agent
**Priority**: Medium
**Dependencies**: Task 1

**File to Create**: `src/tests/unit/application/test_delete_load_use_case.py`

```python
"""
File: test_delete_load_use_case.py
Description: Unit tests for DeleteLoadUseCase
Author: HappyRobot Team
Created: 2024-08-20
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.core.application.use_cases.delete_load_use_case import (
    DeleteLoadUseCase,
    DeleteLoadRequest,
    DeleteLoadResponse,
    LoadNotFoundException,
    LoadDeletionException
)
from src.core.domain.entities import Load, LoadStatus
from src.tests.unit.application.test_create_load_use_case import MockLoadRepository


@pytest.fixture
def mock_repository():
    return MockLoadRepository()


@pytest.fixture
def delete_load_use_case(mock_repository):
    return DeleteLoadUseCase(mock_repository)


@pytest.fixture
def sample_load():
    """Create a sample load for testing."""
    from src.core.domain.value_objects import Location, EquipmentType, Rate

    return Load(
        load_id=uuid4(),
        reference_number="LD-2024-08-00001",
        origin=Location(city="Chicago", state="IL", zip_code="60601"),
        destination=Location(city="Los Angeles", state="CA", zip_code="90210"),
        pickup_date=datetime.utcnow().date(),
        delivery_date=datetime.utcnow().date(),
        equipment_type=EquipmentType.from_name("53-foot van"),
        loadboard_rate=Rate.from_float(2500.00),
        weight=40000,
        commodity_type="General Freight",
        status=LoadStatus.AVAILABLE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.mark.unit
async def test_delete_load_success(delete_load_use_case, mock_repository, sample_load):
    """Test successful load deletion."""
    # Arrange
    await mock_repository.create(sample_load)
    request = DeleteLoadRequest(load_id=sample_load.load_id)

    # Act
    response = await delete_load_use_case.execute(request)

    # Assert
    assert response.deleted is True
    assert response.load_id == str(sample_load.load_id)
    assert response.deletion_type == "soft"


@pytest.mark.unit
async def test_delete_load_not_found(delete_load_use_case):
    """Test deletion of non-existent load."""
    # Arrange
    non_existent_id = uuid4()
    request = DeleteLoadRequest(load_id=non_existent_id)

    # Act & Assert
    with pytest.raises(LoadNotFoundException) as exc_info:
        await delete_load_use_case.execute(request)

    assert str(non_existent_id) in str(exc_info.value)


@pytest.mark.unit
async def test_delete_load_in_transit(delete_load_use_case, mock_repository, sample_load):
    """Test deletion fails for load in transit."""
    # Arrange
    sample_load.status = LoadStatus.IN_TRANSIT
    await mock_repository.create(sample_load)
    request = DeleteLoadRequest(load_id=sample_load.load_id)

    # Act & Assert
    with pytest.raises(LoadDeletionException) as exc_info:
        await delete_load_use_case.execute(request)

    assert "in transit" in str(exc_info.value).lower()


@pytest.mark.unit
async def test_delete_delivered_load(delete_load_use_case, mock_repository, sample_load):
    """Test deletion fails for delivered load."""
    # Arrange
    sample_load.status = LoadStatus.DELIVERED
    await mock_repository.create(sample_load)
    request = DeleteLoadRequest(load_id=sample_load.load_id)

    # Act & Assert
    with pytest.raises(LoadDeletionException) as exc_info:
        await delete_load_use_case.execute(request)

    assert "delivered" in str(exc_info.value).lower()
```

---

### Task 5: Create Integration Tests for DELETE Endpoint
**Agent**: qa-agent
**Priority**: Medium
**Dependencies**: Tasks 3, 4

**File to Create**: `src/tests/integration/test_delete_load_endpoint.py`

```python
"""
File: test_delete_load_endpoint.py
Description: Integration tests for DELETE load endpoint
Author: HappyRobot Team
Created: 2024-08-20
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta

from src.config.settings import settings


@pytest.fixture
async def created_load(test_client: AsyncClient, api_headers):
    """Create a load for testing deletion."""
    # Create load first
    future_date = datetime.utcnow() + timedelta(days=5)
    delivery_date = future_date + timedelta(days=2)

    create_payload = {
        "origin": {
            "city": "Chicago",
            "state": "IL",
            "zip": "60601"
        },
        "destination": {
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90210"
        },
        "pickup_datetime": future_date.isoformat(),
        "delivery_datetime": delivery_date.isoformat(),
        "equipment_type": "53-foot van",
        "loadboard_rate": 2500.00,
        "weight": 40000,
        "commodity_type": "General Freight",
        "notes": "Test load for deletion"
    }

    response = await test_client.post(
        "/api/v1/loads/",
        json=create_payload,
        headers=api_headers
    )

    assert response.status_code == 201
    return response.json()


@pytest.mark.integration
async def test_delete_load_success(test_client: AsyncClient, api_headers, created_load):
    """Test successful load deletion."""
    # Act
    response = await test_client.delete(
        f"/api/v1/loads/{created_load['load_id']}",
        headers=api_headers
    )

    # Assert
    assert response.status_code == 204
    assert response.content == b''

    # Verify load is deleted (should return 404)
    get_response = await test_client.get(
        f"/api/v1/loads/{created_load['load_id']}",
        headers=api_headers
    )
    assert get_response.status_code == 404


@pytest.mark.integration
async def test_delete_load_not_found(test_client: AsyncClient, api_headers):
    """Test deletion of non-existent load."""
    # Arrange
    non_existent_id = str(uuid4())

    # Act
    response = await test_client.delete(
        f"/api/v1/loads/{non_existent_id}",
        headers=api_headers
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_delete_load_invalid_id(test_client: AsyncClient, api_headers):
    """Test deletion with invalid UUID format."""
    # Act
    response = await test_client.delete(
        "/api/v1/loads/invalid-uuid",
        headers=api_headers
    )

    # Assert
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_delete_load_unauthorized(test_client: AsyncClient):
    """Test deletion without authentication."""
    # Act
    response = await test_client.delete(
        f"/api/v1/loads/{uuid4()}"
    )

    # Assert
    assert response.status_code == 403  # Or 401 depending on auth implementation


@pytest.mark.integration
async def test_delete_load_idempotency(test_client: AsyncClient, api_headers, created_load):
    """Test that deleting an already deleted load returns appropriate response."""
    # First deletion
    response1 = await test_client.delete(
        f"/api/v1/loads/{created_load['load_id']}",
        headers=api_headers
    )
    assert response1.status_code == 204

    # Second deletion attempt
    response2 = await test_client.delete(
        f"/api/v1/loads/{created_load['load_id']}",
        headers=api_headers
    )
    assert response2.status_code == 404  # Load already deleted
```

---

### Task 6: Add GET by ID Endpoint (Optional Enhancement)
**Agent**: backend-agent
**Priority**: Low
**Dependencies**: None

Since the integration test references a GET by ID endpoint that doesn't exist, we should add it:

**File to Modify**: `src/interfaces/api/v1/loads.py`

**Location**: Add after the list endpoint (after line 270)

```python
@router.get("/{load_id}", response_model=LoadSummaryModel)
async def get_load(
    load_id: str,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Get a specific load by ID.

    Path Parameters:
        load_id: The UUID of the load to retrieve

    Returns:
        LoadSummaryModel: The load details

    Raises:
        HTTPException: 400 for invalid UUID, 404 if not found
    """
    try:
        # Validate UUID format
        from uuid import UUID as uuid_validator
        try:
            load_uuid = uuid_validator(load_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid load ID format: {load_id}")

        # Get load from repository
        load_repo = PostgresLoadRepository(session)
        load = await load_repo.get_by_id(load_uuid)

        if not load:
            raise HTTPException(status_code=404, detail=f"Load not found: {load_id}")

        # Check if deleted
        if load.deleted_at is not None:
            raise HTTPException(status_code=404, detail=f"Load not found: {load_id}")

        # Convert to response model
        return LoadSummaryModel(
            load_id=str(load.load_id),
            origin=f"{load.origin.city}, {load.origin.state}",
            destination=f"{load.destination.city}, {load.destination.state}",
            pickup_datetime=datetime.combine(load.pickup_date, load.pickup_time_start or datetime.min.time()),
            delivery_datetime=datetime.combine(load.delivery_date, load.delivery_time_start or datetime.min.time()),
            equipment_type=load.equipment_type.name,
            loadboard_rate=load.loadboard_rate.to_float(),
            notes=load.notes,
            weight=load.weight,
            commodity_type=load.commodity_type,
            status=load.status.value,
            created_at=load.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```

---

### Task 7: Update Database Migration (if needed)
**Agent**: backend-agent
**Priority**: Low
**Dependencies**: None

Check if the `deleted_at` column exists in the loads table. If not, create a migration:

**File to Create**: `migrations/versions/xxx_add_deleted_at_to_loads.py`

```python
"""Add deleted_at column to loads table

Revision ID: xxx
Revises: previous_revision_id
Create Date: 2024-08-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxx'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    # Add deleted_at column if it doesn't exist
    op.add_column('loads', sa.Column('deleted_at',
                                     sa.TIMESTAMP(timezone=True),
                                     nullable=True))

    # Create index for better query performance
    op.create_index('ix_loads_deleted_at', 'loads', ['deleted_at'])


def downgrade():
    op.drop_index('ix_loads_deleted_at', table_name='loads')
    op.drop_column('loads', 'deleted_at')
```

---

## API Contract

### DELETE /api/v1/loads/{load_id}

**Request**:
- Method: DELETE
- Path: `/api/v1/loads/{load_id}`
- Headers:
  - `X-API-Key: <api_key>` or `Authorization: ApiKey <api_key>`
- Path Parameters:
  - `load_id` (string, required): UUID of the load to delete

**Response**:
- Success (204 No Content): Empty response body
- Error Responses:
  - 400 Bad Request: Invalid UUID format
  - 403 Forbidden: Missing or invalid API key
  - 404 Not Found: Load doesn't exist
  - 409 Conflict: Load cannot be deleted due to business rules
  - 500 Internal Server Error: Unexpected server error

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/loads/123e4567-e89b-12d3-a456-426614174000" \
     -H "X-API-Key: dev-local-api-key"
```

---

## Database Considerations

### Cascade Behavior
- **Soft Delete**: The load record remains in the database with `deleted_at` timestamp
- **Related Records**:
  - Negotiations: Keep references intact (historical data)
  - Calls: Keep references intact (audit trail)
  - No cascade delete needed for soft deletes

### Indexes
- Ensure index on `deleted_at` column for query performance
- Compound index on `(is_active, deleted_at)` for filtered queries

---

## Testing Strategy

### Unit Tests
1. **DeleteLoadUseCase Tests**:
   - Successful deletion
   - Load not found
   - Business rule violations (in-transit, delivered)
   - Validation errors

2. **Repository Tests**:
   - Soft delete mechanics
   - Already deleted handling
   - Transaction behavior

### Integration Tests
1. **API Endpoint Tests**:
   - Successful deletion flow
   - Authentication required
   - Invalid UUID handling
   - Non-existent load
   - Idempotency

2. **Database Tests**:
   - Verify soft delete
   - Check cascade behavior
   - Transaction rollback on error

### Manual Testing Checklist
- [ ] Delete available load
- [ ] Try to delete non-existent load
- [ ] Try to delete with invalid UUID
- [ ] Try to delete without authentication
- [ ] Try to delete in-transit load
- [ ] Verify deleted load doesn't appear in list
- [ ] Verify related records remain intact

---

## Deployment Considerations

1. **Database Migration**:
   - Run migration to ensure `deleted_at` column exists
   - Add indexes if needed

2. **API Documentation**:
   - Update OpenAPI spec
   - Update API documentation

3. **Monitoring**:
   - Add metrics for deletion operations
   - Monitor for excessive deletion rates

4. **Rollback Plan**:
   - Soft deletes can be reversed by clearing `deleted_at`
   - Keep backup before deployment

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidental deletion | Medium | Soft delete allows recovery |
| Cascade issues | Low | No cascade for soft delete |
| Performance impact | Low | Proper indexes in place |
| Data consistency | Low | Transaction support |

---

## Implementation Order

1. **Phase 1 - Core Implementation** (Tasks 1-3)
   - Create DeleteLoadUseCase
   - Update repository if needed
   - Add DELETE endpoint

2. **Phase 2 - Testing** (Tasks 4-5)
   - Unit tests
   - Integration tests

3. **Phase 3 - Enhancement** (Tasks 6-7)
   - Add GET by ID endpoint
   - Database migration if needed

---

## Success Criteria

- [ ] DELETE endpoint returns 204 on success
- [ ] Proper error codes for various failure scenarios
- [ ] All tests passing (unit and integration)
- [ ] Soft delete preserves data
- [ ] API key authentication enforced
- [ ] No impact on existing functionality

---

## Agent Assignments Summary

- **backend-agent**: Tasks 1, 2, 3, 6, 7 (Core implementation)
- **qa-agent**: Tasks 4, 5 (Testing)

Each agent should create their own summary file:
- backend-agent: `HappyRobot_subagent_backend.md`
- qa-agent: `HappyRobot_subagent_qa.md`

---

## Notes for Implementation

1. The repository already has a `delete` method implementing soft delete
2. Consider adding a `hard_delete` method for permanent deletion if needed
3. The LoadStatus enum should include 'CANCELLED' status
4. Consider adding audit logging for delete operations
5. Future enhancement: Add bulk delete capability

---

**Document Version**: 1.0
**Created**: 2024-08-20
**Author**: Implementation Planner Agent
