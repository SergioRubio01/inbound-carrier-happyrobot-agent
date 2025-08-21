# Implementation Plan: DELETE Metrics Endpoint

## Executive Summary

This implementation plan outlines the addition of a DELETE endpoint to the HappyRobot FDE metrics API. The new endpoint will allow authorized users to delete specific call metrics records by their unique identifier (metrics_id). This enhancement provides data management capabilities while maintaining the existing security and architectural patterns of the system.

**Key Deliverable**: DELETE `/api/v1/metrics/call/{metrics_id}` endpoint with full testing coverage

**Estimated Effort**: 2-3 hours for complete implementation and testing

## Architecture Overview

The implementation follows the existing hexagonal architecture:
- **API Layer**: FastAPI endpoint in `src/interfaces/api/v1/metrics.py`
- **Repository Layer**: Database operations in `src/infrastructure/database/postgres/call_metrics_repository.py`
- **Model Layer**: Uses existing `CallMetricsModel` without modifications
- **Testing**: Integration and unit tests following pytest conventions

## Task Breakdown

### Task 1: Repository Method Verification
**Agent**: backend-agent
**Priority**: HIGH
**Dependencies**: None
**Files to Modify**:
- `src/infrastructure/database/postgres/call_metrics_repository.py` (verify only - method already exists)

**Description**: Verify that the `delete()` method in PostgresCallMetricsRepository is properly implemented and functional. The method already exists (lines 161-173) and follows the correct pattern:
- Accepts UUID parameter
- Returns boolean (True if deleted, False if not found)
- Properly handles database transactions

**Validation**:
- Confirm method signature matches: `async def delete(self, record_id: UUID) -> bool`
- Verify proper error handling
- Check flush operation before commit

### Task 2: API Endpoint Implementation
**Agent**: backend-agent
**Priority**: HIGH
**Dependencies**: Task 1
**Files to Modify**:
- `src/interfaces/api/v1/metrics.py`

**Implementation Details**:

Add the following endpoint after the existing GET endpoints (around line 365):

```python
@router.delete("/call/{metrics_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call_metrics(
    metrics_id: UUID,
    session: AsyncSession = Depends(get_database_session),
) -> None:
    """
    Delete specific call metrics by ID.

    Returns:
        - 204 No Content: Metrics successfully deleted
        - 404 Not Found: Metrics with given ID does not exist
        - 500 Internal Server Error: Database or system error
    """
    try:
        # Initialize repository
        call_metrics_repo = PostgresCallMetricsRepository(session)

        # Attempt to delete the metrics
        deleted = await call_metrics_repo.delete(metrics_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call metrics with ID {metrics_id} not found"
            )

        # Commit the transaction
        await session.commit()

        # Return 204 No Content on successful deletion
        return None

    except HTTPException:
        # Re-raise HTTP exceptions
        await session.rollback()
        raise
    except Exception as e:
        # Handle unexpected errors
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metrics: {str(e)}"
        )
```

**Key Implementation Points**:
- UUID validation is handled automatically by FastAPI's type hint
- Proper transaction management with commit/rollback
- Returns 204 No Content on success (standard REST practice)
- Returns 404 if metrics_id doesn't exist
- Includes comprehensive error handling
- Follows existing code patterns in the file

### Task 3: Integration Testing
**Agent**: qa-agent
**Priority**: HIGH
**Dependencies**: Task 2
**Files to Create/Modify**:
- `src/tests/integration/test_call_metrics_delete.py` (new file)

**Test Cases to Implement**:

```python
"""
Integration tests for DELETE call metrics endpoint
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

@pytest.mark.integration
class TestDeleteCallMetrics:

    def test_delete_existing_metrics_success(self, client, db_session):
        """Test successful deletion of existing metrics."""
        # First create a metric
        create_data = {
            "transcript": "Test transcript for deletion",
            "response": "ACCEPTED"
        }
        create_response = client.post("/api/v1/metrics/call", json=create_data)
        assert create_response.status_code == 201
        metrics_id = create_response.json()["metrics_id"]

        # Delete the metric
        delete_response = client.delete(f"/api/v1/metrics/call/{metrics_id}")
        assert delete_response.status_code == 204
        assert delete_response.content == b''

        # Verify it's deleted (GET should return 404)
        get_response = client.get(f"/api/v1/metrics/call/{metrics_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_metrics_returns_404(self, client):
        """Test deletion of non-existent metrics returns 404."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/metrics/call/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_invalid_uuid_returns_422(self, client):
        """Test deletion with invalid UUID returns validation error."""
        response = client.delete("/api/v1/metrics/call/not-a-uuid")
        assert response.status_code == 422

    def test_delete_requires_authentication(self, unauthenticated_client):
        """Test that DELETE endpoint requires API key authentication."""
        fake_id = str(uuid4())
        response = unauthenticated_client.delete(f"/api/v1/metrics/call/{fake_id}")
        assert response.status_code == 401

    def test_delete_idempotency(self, client, db_session):
        """Test that deleting already deleted metrics returns 404."""
        # Create and delete a metric
        create_data = {
            "transcript": "Test transcript",
            "response": "REJECTED"
        }
        create_response = client.post("/api/v1/metrics/call", json=create_data)
        metrics_id = create_response.json()["metrics_id"]

        # First deletion should succeed
        first_delete = client.delete(f"/api/v1/metrics/call/{metrics_id}")
        assert first_delete.status_code == 204

        # Second deletion should return 404
        second_delete = client.delete(f"/api/v1/metrics/call/{metrics_id}")
        assert second_delete.status_code == 404
```

### Task 4: Unit Testing for Repository
**Agent**: qa-agent
**Priority**: MEDIUM
**Dependencies**: Task 3
**Files to Modify**:
- `src/tests/unit/infrastructure/test_call_metrics_repository.py`

**Test Cases to Add**:

```python
@pytest.mark.unit
async def test_delete_existing_metrics(repository, sample_metrics):
    """Test deleting existing metrics returns True."""
    # Create a metric
    created = await repository.create_metrics(
        transcript="Test",
        response="ACCEPTED"
    )

    # Delete it
    result = await repository.delete(created.metrics_id)
    assert result is True

    # Verify it's deleted
    found = await repository.get_by_id(created.metrics_id)
    assert found is None

@pytest.mark.unit
async def test_delete_nonexistent_metrics(repository):
    """Test deleting non-existent metrics returns False."""
    fake_id = uuid4()
    result = await repository.delete(fake_id)
    assert result is False

@pytest.mark.unit
async def test_exists_method(repository, sample_metrics):
    """Test exists method works correctly."""
    # Create a metric
    created = await repository.create_metrics(
        transcript="Test",
        response="ACCEPTED"
    )

    # Should exist
    assert await repository.exists(created.metrics_id) is True

    # Delete it
    await repository.delete(created.metrics_id)

    # Should not exist
    assert await repository.exists(created.metrics_id) is False
```

### Task 5: API Documentation Update
**Agent**: backend-agent
**Priority**: LOW
**Dependencies**: Task 2
**Files to Modify**: None (handled automatically by FastAPI)

**Verification Steps**:
1. Ensure the endpoint docstring is comprehensive
2. Verify OpenAPI schema generation includes the new endpoint
3. Test that `/api/v1/docs` displays the new endpoint correctly

### Task 6: End-to-End Testing and Validation
**Agent**: qa-agent
**Priority**: HIGH
**Dependencies**: Tasks 1-5
**Files**: All modified files

**Validation Checklist**:
- [ ] DELETE endpoint is accessible at `/api/v1/metrics/call/{metrics_id}`
- [ ] Endpoint requires API key authentication
- [ ] Returns 204 on successful deletion
- [ ] Returns 404 when metrics_id doesn't exist
- [ ] Returns 422 for invalid UUID format
- [ ] Database transaction is properly committed
- [ ] Rollback occurs on errors
- [ ] All tests pass (`pytest src/tests/integration/test_call_metrics_delete.py`)
- [ ] Linting passes (`ruff check src/interfaces/api/v1/metrics.py`)
- [ ] Type checking passes (`mypy src/interfaces/api/v1/metrics.py`)

## API Contract

### DELETE /api/v1/metrics/call/{metrics_id}

**Authentication**: Required (API Key via `X-API-Key` header or `Authorization: ApiKey <key>`)

**Path Parameters**:
- `metrics_id` (UUID, required): The unique identifier of the metrics record to delete

**Response Codes**:
- `204 No Content`: Metrics successfully deleted
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Metrics with given ID does not exist
- `422 Unprocessable Entity`: Invalid UUID format
- `500 Internal Server Error`: Database or system error

**Response Body**: None (empty body on success)

**Example Request**:
```bash
curl -X DELETE \
  "http://localhost:8000/api/v1/metrics/call/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: dev-local-api-key"
```

## Testing Strategy

### Unit Tests
- Repository method isolation with mocked database
- Edge cases: non-existent IDs, database errors
- Transaction management verification

### Integration Tests
- Full request/response cycle
- Authentication verification
- Error handling scenarios
- Database state verification

### Manual Testing Steps
1. Start local environment: `docker compose up --build`
2. Create a test metric via POST endpoint
3. Retrieve the metrics_id from response
4. Delete the metric using DELETE endpoint
5. Verify deletion by attempting to GET the same metrics_id
6. Test error scenarios (invalid UUID, missing auth, etc.)

## Risk Assessment

### Low Risk
- Implementation uses existing patterns and infrastructure
- No database schema changes required
- Repository method already exists and tested
- Follows REST standards

### Mitigation Strategies
- Comprehensive error handling with rollback
- Extensive test coverage
- No breaking changes to existing endpoints
- Proper transaction management

## Implementation Order

1. **Backend-agent**: Verify repository method (Task 1) - 15 minutes
2. **Backend-agent**: Implement DELETE endpoint (Task 2) - 30 minutes
3. **QA-agent**: Create integration tests (Task 3) - 45 minutes
4. **QA-agent**: Add unit tests (Task 4) - 30 minutes
5. **Backend-agent**: Verify API documentation (Task 5) - 10 minutes
6. **QA-agent**: End-to-end validation (Task 6) - 30 minutes

Total estimated time: 2-3 hours

## Success Criteria

- [ ] DELETE endpoint successfully removes metrics from database
- [ ] All existing tests continue to pass
- [ ] New tests provide >90% coverage of new code
- [ ] API documentation is automatically updated
- [ ] No performance degradation
- [ ] Follows all project conventions and patterns

## Notes for Subagents

Each assigned agent must create their summary file:
- **backend-agent**: Create `HappyRobot_subagent_2.md` after completing Tasks 1, 2, and 5
- **qa-agent**: Create `HappyRobot_subagent_3.md` after completing Tasks 3, 4, and 6

Include in your summary:
- Tasks completed
- Any issues encountered
- Code changes made
- Test results
- Recommendations for future improvements
