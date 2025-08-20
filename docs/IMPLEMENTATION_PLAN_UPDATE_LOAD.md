# Implementation Plan: PUT Endpoint for Load Updates

## Executive Summary

This document outlines the implementation plan for adding a PUT endpoint to update existing load registries in the HappyRobot FDE platform. The new endpoint will follow the existing hexagonal architecture patterns, provide comprehensive validation, and ensure data integrity through business rule enforcement. The implementation will enable authorized users to update load information while maintaining audit trails and preventing invalid state transitions.

## Architecture Overview

The implementation follows the established hexagonal architecture:
- **API Layer**: FastAPI endpoint handling HTTP requests
- **Application Layer**: Use case containing business logic
- **Domain Layer**: Entity validation and business rules
- **Infrastructure Layer**: Database persistence via repository pattern

## API Contract

### Endpoint Definition
```
PUT /api/v1/loads/{load_id}
```

### Request Schema
```python
class UpdateLoadRequestModel(BaseModel):
    """Request model for updating an existing load."""
    # Location Information
    origin: LocationRequestModel
    destination: LocationRequestModel

    # Schedule
    pickup_datetime: datetime
    delivery_datetime: datetime

    # Equipment & Load Details
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str

    # Optional Fields
    notes: Optional[str] = None
    broker_company: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    customer_name: Optional[str] = None
    dimensions: Optional[str] = None
    pieces: Optional[int] = None
    hazmat: bool = False
    hazmat_class: Optional[str] = None
    miles: Optional[int] = None
    fuel_surcharge: Optional[float] = None

    # Status (restricted updates)
    status: Optional[str] = None  # Only certain transitions allowed
```

### Response Schema
```python
class UpdateLoadResponseModel(BaseModel):
    """Response model for load update."""
    load_id: str
    reference_number: str
    status: str
    updated_at: datetime
    version: int  # Optimistic locking version
```

### Error Responses
- `400 Bad Request`: Invalid input data or business rule violation
- `404 Not Found`: Load ID does not exist
- `409 Conflict`: Version mismatch or invalid status transition
- `500 Internal Server Error`: Unexpected server error

## Database Schema Considerations

No database schema changes required. The existing `loads` table supports all necessary fields. The `version` field will be used for optimistic locking to prevent concurrent update conflicts.

## Business Rules

### Immutable Fields
The following fields cannot be updated once a load is created:
- `load_id`
- `reference_number`
- `created_at`
- `created_by`
- `source`

### Status Transition Rules
Valid status transitions:
- `AVAILABLE` → `PENDING`, `BOOKED`, `CANCELLED`
- `PENDING` → `AVAILABLE`, `BOOKED`, `CANCELLED`
- `BOOKED` → `IN_TRANSIT`, `CANCELLED`
- `IN_TRANSIT` → `DELIVERED`
- `CANCELLED` → Cannot be changed
- `DELIVERED` → Cannot be changed

### Update Restrictions
- Cannot update deleted loads (`deleted_at` is not null)
- Cannot update loads with status `DELIVERED`
- Cannot update loads with status `IN_TRANSIT` (except status change to `DELIVERED`)
- Weight must not exceed configured maximum (80,000 lbs)
- Pickup datetime must be before delivery datetime
- Cannot set pickup datetime in the past (unless already past)

## Implementation Tasks

### Task 1: Create UpdateLoadUseCase
**Agent**: backend-agent
**Priority**: High
**Dependencies**: None
**Files to Create**:
- `src/core/application/use_cases/update_load_use_case.py`

**Implementation Details**:
```python
# Key components:
- UpdateLoadRequest dataclass with all updatable fields
- UpdateLoadResponse dataclass with updated load info
- UpdateLoadUseCase class with execute method
- Validation methods for business rules
- Optimistic locking check using version field
```

### Task 2: Extend Repository with Full Update Support
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Task 1
**Files to Modify**:
- `src/infrastructure/database/postgres/load_repository.py`

**Implementation Details**:
- Ensure the `update` method properly handles version increment
- Add version checking to prevent concurrent updates
- Ensure `updated_at` timestamp is set

### Task 3: Implement PUT Endpoint
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Tasks 1, 2
**Files to Modify**:
- `src/interfaces/api/v1/loads.py`

**Implementation Details**:
```python
@router.put("/{load_id}", response_model=UpdateLoadResponseModel)
async def update_load(
    load_id: UUID = Path(..., description="Load ID"),
    request: UpdateLoadRequestModel,
    session: AsyncSession = Depends(get_database_session)
):
    """Update an existing load."""
    # Implementation following existing patterns
```

### Task 4: Unit Tests for UpdateLoadUseCase
**Agent**: qa-agent
**Priority**: High
**Dependencies**: Task 1
**Files to Create**:
- `src/tests/unit/application/test_update_load_use_case.py`

**Test Scenarios**:
1. Successful update with all fields
2. Successful partial update (only required fields)
3. Load not found error
4. Invalid status transition
5. Update deleted load (should fail)
6. Update delivered load (should fail)
7. Version conflict (optimistic locking)
8. Validation errors (dates, weight, etc.)

### Task 5: Integration Tests for PUT Endpoint
**Agent**: qa-agent
**Priority**: High
**Dependencies**: Tasks 3, 4
**Files to Create**:
- `src/tests/integration/test_update_load_endpoint.py`

**Test Scenarios**:
1. Full update via API
2. Authentication validation
3. Invalid load ID format
4. Concurrent update handling
5. Status transition validation via API

### Task 6: Update API Documentation
**Agent**: backend-agent
**Priority**: Medium
**Dependencies**: Task 3
**Files to Modify**:
- Update OpenAPI/Swagger documentation (automatic via FastAPI)
- Ensure proper descriptions in endpoint docstrings

## Testing Strategy

### Unit Testing
- Mock repository interactions
- Test all business rule validations
- Test error handling paths
- Verify optimistic locking logic

### Integration Testing
- Test full request/response cycle
- Verify database updates
- Test concurrent update scenarios
- Validate API authentication

### Manual Testing Checklist
1. Update load with all fields
2. Update load with minimal fields
3. Attempt invalid status transitions
4. Test version conflict resolution
5. Verify audit trail (updated_at, version)

## Deployment Considerations

### Configuration
No new configuration parameters required.

### Database Migration
No database migration needed - existing schema supports all requirements.

### Performance
- Index already exists on `load_id` for fast lookups
- Version field enables optimistic locking without additional locks
- Expected response time: < 200ms for typical updates

### Monitoring
- Log all update attempts with user context
- Monitor for high rates of version conflicts
- Track invalid status transition attempts

## Risk Assessment

### Technical Risks
1. **Concurrent Updates**: Mitigated by optimistic locking with version field
2. **Data Integrity**: Strict validation and business rules enforcement
3. **Performance**: Minimal impact, single row updates with indexed lookups

### Business Risks
1. **Invalid State Transitions**: Prevented by business rule validation
2. **Audit Trail**: Maintained through updated_at and version tracking
3. **Unauthorized Updates**: API key authentication required

## Implementation Sequence

1. **Phase 1**: Core Implementation (Tasks 1-3)
   - Create use case
   - Verify repository support
   - Implement endpoint

2. **Phase 2**: Testing (Tasks 4-5)
   - Unit tests
   - Integration tests
   - Manual validation

3. **Phase 3**: Documentation (Task 6)
   - API documentation
   - Update existing docs if needed

## Success Criteria

- [ ] PUT endpoint successfully updates loads
- [ ] All business rules enforced
- [ ] Optimistic locking prevents concurrent update conflicts
- [ ] Unit test coverage > 90%
- [ ] Integration tests pass
- [ ] API documentation updated
- [ ] No performance degradation

## Code Examples

### Use Case Request/Response
```python
@dataclass
class UpdateLoadRequest:
    """Request for updating a load."""
    load_id: UUID
    origin: Location
    destination: Location
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str
    # ... other fields
    version: int  # For optimistic locking

@dataclass
class UpdateLoadResponse:
    """Response for load update."""
    load_id: str
    reference_number: str
    status: str
    updated_at: datetime
    version: int
```

### Business Rule Validation Example
```python
async def _validate_update_rules(self, existing_load: Load, request: UpdateLoadRequest) -> None:
    """Validate business rules for load update."""
    # Cannot update deleted loads
    if existing_load.deleted_at is not None:
        raise LoadUpdateException("Cannot update deleted load")

    # Cannot update delivered loads
    if existing_load.status == LoadStatus.DELIVERED:
        raise LoadUpdateException("Cannot update delivered load")

    # Validate status transition if status is being changed
    if request.status and request.status != existing_load.status.value:
        if not self._is_valid_status_transition(existing_load.status, LoadStatus(request.status)):
            raise LoadUpdateException(f"Invalid status transition from {existing_load.status.value} to {request.status}")

    # Check version for optimistic locking
    if request.version != existing_load.version:
        raise LoadVersionConflictException("Load has been modified by another user")
```

## Notes for Agents

### Backend Agent
- Follow existing patterns from CreateLoadUseCase and DeleteLoadUseCase
- Ensure proper error handling and logging
- Maintain consistency with existing validation approaches
- Remember to create your `HappyRobot_subagent_2.md` summary file

### QA Agent
- Focus on edge cases and error scenarios
- Ensure comprehensive coverage of business rules
- Test concurrent update scenarios thoroughly
- Remember to create your `HappyRobot_subagent_3.md` summary file

## Conclusion

This implementation plan provides a comprehensive approach to adding PUT endpoint functionality for load updates. The design follows established patterns, ensures data integrity through business rules, and provides robust error handling. The modular task breakdown allows for parallel development and systematic testing.
