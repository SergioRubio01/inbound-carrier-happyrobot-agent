# Loads API Refactoring Implementation Plan

## Executive Summary

This document outlines the comprehensive plan to refactor the loads API endpoints in the HappyRobot FDE platform. The refactoring will replace the existing search-only endpoint with two new endpoints that provide full CRUD functionality for load management. The implementation follows the hexagonal architecture pattern, ensuring clean separation of concerns between business logic and infrastructure layers.

**Objective**: Implement `POST /api/v1/loads` and `GET /api/v1/loads` endpoints with complete load management capabilities while maintaining the existing hexagonal architecture.

**Timeline**: Estimated 2-3 days with 2 backend agents working in parallel.

**Impact**: This refactoring will enable the HappyRobot platform to create and manage loads directly through the API, providing a foundation for load management automation.

## Current State Analysis

### Existing Implementation
- **Current Endpoint**: `POST /api/v1/loads/search` - Search-only functionality
- **Architecture**: Hexagonal architecture with proper separation of layers
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Domain Model**: Comprehensive Load entity with all required fields
- **Repository Pattern**: Interface-based repository with PostgreSQL implementation

### Key Findings
1. **Database Schema**: Already contains all required fields including:
   - pickup_date (exists as Date)
   - delivery_date (exists as Date)
   - commodity_type (exists as String)
   - Notes: pickup_datetime and delivery_datetime will be composed from date + time fields

2. **Domain Entity**: Load entity is well-structured with all necessary fields and business logic

3. **Repository**: Existing repository has create, update, and list methods but they need to be enhanced

4. **Use Cases**: Only SearchLoadsUseCase exists; need to create new use cases for creation and listing

## Implementation Tasks

### Task 1: Create Load Creation Use Case
**Agent**: backend-agent-1
**Priority**: High
**Dependencies**: None

**Files to Create**:
- `src/core/application/use_cases/create_load.py`

**Implementation Details**:
```python
# Key components to implement:
- CreateLoadRequest dataclass with all required fields
- CreateLoadResponse dataclass
- CreateLoadUseCase class with validation logic
- Business rules for load creation
- Error handling for duplicate reference numbers
```

**Deliverables**:
- Complete use case implementation with input validation
- Business logic for auto-generating reference numbers if not provided
- Proper error handling and domain exceptions

---

### Task 2: Create Load Listing Use Case
**Agent**: backend-agent-2
**Priority**: High
**Dependencies**: None (can work in parallel with Task 1)

**Files to Create**:
- `src/core/application/use_cases/list_loads.py`

**Implementation Details**:
```python
# Key components to implement:
- ListLoadsRequest dataclass with pagination and filtering
- ListLoadsResponse dataclass with load summaries
- ListLoadsUseCase class
- Support for sorting and filtering by status
```

**Deliverables**:
- Complete use case for listing loads with pagination
- Filtering by status, date range, and equipment type
- Sorting options (by date, rate, distance)

---

### Task 3: Update API Endpoints
**Agent**: backend-agent-1
**Priority**: High
**Dependencies**: Tasks 1 and 2

**Files to Modify**:
- `src/interfaces/api/v1/loads.py`

**Implementation Details**:
```python
# Add new endpoints:

@router.post("", response_model=CreateLoadResponseModel)
async def create_load(
    request: CreateLoadRequestModel,
    session: AsyncSession = Depends(get_database_session)
):
    """Create a new load in the system."""
    # Implementation using CreateLoadUseCase

@router.get("", response_model=ListLoadsResponseModel)
async def list_loads(
    status: Optional[str] = Query(None),
    equipment_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at_desc"),
    session: AsyncSession = Depends(get_database_session)
):
    """List all loads with optional filtering."""
    # Implementation using ListLoadsUseCase
```

**Request/Response Models**:
```python
class CreateLoadRequestModel(BaseModel):
    origin: LocationModel
    destination: LocationModel
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    broker_company: Optional[str] = None
    special_requirements: Optional[List[str]] = None

class LoadSummaryModel(BaseModel):
    load_id: str
    origin: str  # "City, ST"
    destination: str  # "City, ST"
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str]
    weight: int
    commodity_type: str
    status: str
    created_at: datetime

class ListLoadsResponseModel(BaseModel):
    loads: List[LoadSummaryModel]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool
```

**Deliverables**:
- Two new API endpoints with proper validation
- Pydantic models for requests and responses
- Integration with use cases
- Proper error handling and HTTP status codes

---

### Task 4: Enhance Repository Implementation
**Agent**: backend-agent-2
**Priority**: Medium
**Dependencies**: None

**Files to Modify**:
- `src/infrastructure/database/postgres/load_repository.py`

**Enhancements Needed**:
1. Improve the `create` method to handle reference number generation
2. Add `list_all` method with pagination and filtering
3. Add index suggestions for performance

**Implementation Details**:
```python
async def list_all(
    self,
    status: Optional[LoadStatus] = None,
    equipment_type: Optional[EquipmentType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at_desc"
) -> Tuple[List[Load], int]:
    """List all loads with filters and return total count."""
    # Implementation with SQLAlchemy query builder
```

**Deliverables**:
- Enhanced repository methods
- Optimized queries with proper indexing
- Support for complex filtering and sorting

---

### Task 5: Database Migration
**Agent**: backend-agent-1
**Priority**: Low
**Dependencies**: Task 4

**Files to Create**:
- `migrations/versions/003_add_load_indexes.py`

**Migration Requirements**:
```sql
-- Add indexes for performance
CREATE INDEX idx_loads_status_created ON loads(status, created_at DESC);
CREATE INDEX idx_loads_equipment_type ON loads(equipment_type);
CREATE INDEX idx_loads_pickup_date ON loads(pickup_date);
CREATE INDEX idx_loads_reference_number ON loads(reference_number);
```

**Deliverables**:
- Alembic migration file
- Performance indexes for common queries
- Rollback strategy

---

### Task 6: Create Integration Tests
**Agent**: backend-agent-2
**Priority**: Medium
**Dependencies**: Tasks 3 and 4

**Files to Create**:
- `src/tests/integration/test_load_endpoints.py`
- `src/tests/unit/test_create_load_use_case.py`
- `src/tests/unit/test_list_loads_use_case.py`

**Test Coverage**:
```python
# Integration tests:
- test_create_load_success
- test_create_load_duplicate_reference
- test_create_load_invalid_data
- test_list_loads_with_filters
- test_list_loads_pagination

# Unit tests:
- Use case validation logic
- Business rule enforcement
- Error handling scenarios
```

**Deliverables**:
- Comprehensive test suite with >80% coverage
- Integration tests for API endpoints
- Unit tests for use cases
- Test fixtures and factories

---

### Task 7: Update API Documentation
**Agent**: backend-agent-1
**Priority**: Low
**Dependencies**: Task 3

**Files to Modify**:
- Update docstrings in `src/interfaces/api/v1/loads.py`
- Ensure OpenAPI schema is properly generated

**Documentation Updates**:
- Endpoint descriptions with example requests/responses
- Field validations and constraints
- Error response documentation
- Authentication requirements

**Deliverables**:
- Complete API documentation
- OpenAPI schema updates
- Example requests in docstrings

## API Contract Specification

### POST /api/v1/loads
**Purpose**: Create a new load in the system

**Request Body**:
```json
{
  "origin": {
    "city": "Chicago",
    "state": "IL",
    "zip": "60601"
  },
  "destination": {
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90001"
  },
  "pickup_datetime": "2024-08-20T10:00:00Z",
  "delivery_datetime": "2024-08-22T18:00:00Z",
  "equipment_type": "53-foot van",
  "loadboard_rate": 3500.00,
  "weight": 35000,
  "commodity_type": "General Freight",
  "notes": "No touch freight, dock to dock",
  "broker_company": "ABC Logistics",
  "special_requirements": ["Tarps required", "Team drivers preferred"]
}
```

**Response** (201 Created):
```json
{
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "reference_number": "LD-2024-08001",
  "status": "AVAILABLE",
  "created_at": "2024-08-14T12:00:00Z"
}
```

### GET /api/v1/loads
**Purpose**: List all loads with filtering and pagination

**Query Parameters**:
- `status`: Filter by load status (AVAILABLE, BOOKED, etc.)
- `equipment_type`: Filter by equipment type
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort_by`: Sort field (created_at_desc, pickup_date_asc, etc.)

**Response** (200 OK):
```json
{
  "loads": [
    {
      "load_id": "550e8400-e29b-41d4-a716-446655440000",
      "origin": "Chicago, IL",
      "destination": "Los Angeles, CA",
      "pickup_datetime": "2024-08-20T10:00:00Z",
      "delivery_datetime": "2024-08-22T18:00:00Z",
      "equipment_type": "53-foot van",
      "loadboard_rate": 3500.00,
      "notes": "No touch freight, dock to dock",
      "weight": 35000,
      "commodity_type": "General Freight",
      "status": "AVAILABLE",
      "created_at": "2024-08-14T12:00:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "has_previous": false
}
```

## Database Schema Requirements

### Existing Fields (No Changes Needed)
- load_id (UUID, PK)
- origin_city, origin_state, origin_zip
- destination_city, destination_state, destination_zip
- pickup_date, pickup_time_start, pickup_time_end
- delivery_date, delivery_time_start, delivery_time_end
- equipment_type
- loadboard_rate
- weight
- commodity_type
- notes
- status
- created_at, updated_at

### New Indexes Required
```sql
CREATE INDEX idx_loads_status_created ON loads(status, created_at DESC);
CREATE INDEX idx_loads_equipment_type ON loads(equipment_type);
CREATE INDEX idx_loads_pickup_date ON loads(pickup_date);
```

## Testing Strategy

### Unit Tests
- **Use Case Tests**: Test business logic in isolation
  - Validation rules
  - Reference number generation
  - Business constraints

### Integration Tests
- **API Tests**: Test complete request/response cycle
  - Valid and invalid inputs
  - Authentication
  - Error responses
  - Pagination edge cases

### Performance Tests
- Load testing with 10,000+ loads
- Query performance validation
- Index effectiveness verification

## Deployment Considerations

### Pre-deployment Checklist
1. Run database migrations
2. Update environment variables if needed
3. Verify API key authentication works
4. Test endpoints in staging environment

### Rollback Plan
1. Keep previous endpoint `/loads/search` operational during transition
2. Database migrations should be reversible
3. Feature flag for switching between old and new implementation

### Monitoring
- Add CloudWatch metrics for new endpoints
- Monitor response times and error rates
- Set up alerts for failed load creations

## Risk Assessment

### Technical Risks
1. **Database Performance**: Large number of loads may impact query performance
   - Mitigation: Proper indexing and pagination limits

2. **Data Validation**: Invalid data could corrupt database
   - Mitigation: Comprehensive validation in use cases

3. **Backward Compatibility**: Existing integrations may break
   - Mitigation: Keep old endpoint operational during transition

### Business Risks
1. **Data Duplication**: Multiple loads with same details
   - Mitigation: Implement duplicate detection logic

2. **Rate Inconsistencies**: Manual rate entry errors
   - Mitigation: Add rate validation and range checks

## Success Criteria

1. Both endpoints operational with <200ms response time
2. All tests passing with >80% coverage
3. Successfully create 100 test loads
4. List endpoint handles 10,000+ loads efficiently
5. API documentation updated and validated
6. No disruption to existing search functionality

## Timeline

### Day 1
- Morning: Tasks 1 & 2 (Use cases) - Parallel execution
- Afternoon: Task 3 (API endpoints)

### Day 2
- Morning: Task 4 (Repository enhancements)
- Afternoon: Tasks 5 & 6 (Migration and tests)

### Day 3
- Morning: Task 7 (Documentation)
- Afternoon: Integration testing and deployment

## Agent Assignments Summary

### backend-agent-1
- Task 1: Create Load Use Case
- Task 3: API Endpoints
- Task 5: Database Migration
- Task 7: Documentation

### backend-agent-2
- Task 2: List Loads Use Case
- Task 4: Repository Enhancements
- Task 6: Testing Suite

## Next Steps

1. Review and approve this implementation plan
2. Assign backend agents to tasks
3. Set up development branches
4. Begin parallel implementation of use cases
5. Daily sync meetings to track progress
6. Final integration and testing

## Appendix: Code Examples

### Example Use Case Structure
```python
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime

@dataclass
class CreateLoadRequest:
    origin: Location
    destination: Location
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str
    notes: Optional[str] = None

class CreateLoadUseCase:
    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: CreateLoadRequest) -> Load:
        # Validation logic
        # Create Load entity
        # Save to repository
        # Return created load
        pass
```

### Example Repository Method
```python
async def list_all(self, filters: Dict[str, Any], limit: int, offset: int) -> Tuple[List[Load], int]:
    query = select(LoadModel).where(LoadModel.deleted_at.is_(None))

    if filters.get('status'):
        query = query.where(LoadModel.status == filters['status'])

    # Add more filters

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await self.session.scalar(count_query)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute and return
    result = await self.session.execute(query)
    models = result.scalars().all()

    loads = [self._model_to_entity(m) for m in models]
    return loads, total
```

This implementation plan provides a clear roadmap for refactoring the loads API endpoints while maintaining the integrity of the hexagonal architecture and ensuring high-quality, maintainable code.
