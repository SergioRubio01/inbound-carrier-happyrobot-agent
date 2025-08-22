# HappyRobot Inbound Carrier Sales POC - Implementation Plan

## Executive Summary

This implementation plan details the enhancement of the HappyRobot Inbound Carrier Sales platform to improve metrics tracking and load management capabilities. The project consists of two phases that will enhance call outcome analysis and load lifecycle management.

**Key Deliverables:**
- Enhanced metrics endpoint with sentiment analysis capabilities
- Improved loads endpoint with booking status and session tracking
- Updated CLI tool for comprehensive metrics reporting
- Database schema updates with proper migrations

**Timeline:** 2-3 days for complete implementation including testing

---

## Phase 1: Metrics Endpoint Improvements

### Objective
Remove the `final_loadboard_rate` field and add sentiment analysis capabilities to better understand call outcomes and customer satisfaction levels.

### API Contract Changes

#### POST /api/v1/metrics/call
**Removed Field:**
- `final_loadboard_rate`: No longer needed in metrics tracking

**New Fields:**
- `sentiment`: string (enum: "Positive", "Neutral", "Negative") - Overall call sentiment
- `sentiment_reason`: string - Explanation for sentiment classification
- `response_reason`: string - Renamed from `reason` for clarity

**Example Request Body:**
```json
{
  "transcript": "[]",
  "response": "Fallback error",
  "response_reason": "The conversation is empty, indicating a fallback error.",
  "sentiment": "Negative",
  "sentiment_reason": "The conversation is empty, indicating a fallback error.",
  "session_id": "c860bbf1-8187-4192-93d6-fa3272742240"
}
```

### Database Schema Changes

**Table: call_metrics**
- Remove column: `final_loadboard_rate`
- Add column: `sentiment VARCHAR(20)` (with CHECK constraint)
- Add column: `sentiment_reason TEXT`
- Rename column: `reason` → `response_reason`

---

## Phase 2: Loads Endpoint Improvements

### Objective
Add booking status tracking and additional load metadata to support complete load lifecycle management.

### API Contract Changes

#### POST /api/v1/loads and PUT /api/v1/loads/{load_id}
**New Fields:**
- `booked`: boolean (default: False) - Indicates if load is booked
- `miles`: string - Distance in miles (stored as string for flexibility)
- `dimensions`: string - Load dimensions information
- `num_of_pieces`: integer - Number of pieces in the load
- `session_id`: string (UUID) - Links load to call session (empty by default)

**Example Request Body:**
```json
{
  "origin": {
    "city": "Sevilla",
    "state": "ST",
    "zip": "41001"
  },
  "destination": {
    "city": "Cordoba",
    "state": "ST",
    "zip": "14001"
  },
  "pickup_datetime": "2025-08-21T21:57:44.672000",
  "delivery_datetime": "2025-08-22T21:57:44.672000",
  "equipment_type": "53-foot van",
  "loadboard_rate": 4000,
  "notes": "Handle with care",
  "weight": 2500,
  "commodity_type": "Electronics",
  "num_of_pieces": 1,
  "miles": "100",
  "dimensions": "standard",
  "booked": true,
  "session_id": "c860bbf1-8187-4192-93d6-fa3272742240"
}
```

### Database Schema Changes

**Table: loads**
- Add column: `booked BOOLEAN DEFAULT FALSE`
- Add column: `miles VARCHAR(20)`
- Add column: `dimensions VARCHAR(255)`
- Add column: `num_of_pieces INTEGER`
- Add column: `session_id UUID`
- Add index: `idx_loads_session_id`
- Add index: `idx_loads_booked`

---

## Implementation Tasks

### Task 1: Database Schema Updates - Phase 1
**Agent:** backend-agent
**Priority:** High
**Files to Create:**
- `migrations/versions/006_update_metrics_sentiment.py`

**Files to Modify:**
- `src/infrastructure/database/models/call_metrics_model.py`

**Deliverables:**
1. Create Alembic migration to:
   - Remove `final_loadboard_rate` column
   - Add `sentiment` and `sentiment_reason` columns
   - Rename `reason` to `response_reason`
2. Update CallMetricsModel with new fields
3. Add CHECK constraint for sentiment values

---

### Task 2: Repository Layer Updates - Phase 1
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/infrastructure/database/postgres/call_metrics_repository.py`

**Deliverables:**
1. Update `create_metrics` method signature
2. Remove `final_loadboard_rate` from all queries
3. Add sentiment fields to creation and retrieval methods
4. Update `get_metrics_summary` to include sentiment distribution

---

### Task 3: API Endpoint Updates - Phase 1
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/interfaces/api/v1/metrics.py`

**Deliverables:**
1. Update `CallMetricsRequestModel`:
   - Remove `final_loadboard_rate` field
   - Add `sentiment` and `sentiment_reason` fields
   - Rename `reason` to `response_reason`
2. Update `CallMetricsResponseModel` accordingly
3. Modify endpoint handlers to use new fields
4. Add validation for sentiment enum values

---

### Task 4: CLI Tool Updates - Phase 1
**Agent:** backend-agent
**Priority:** Medium
**Files to Modify:**
- `src/interfaces/cli.py`

**Deliverables:**
1. Update `_calculate_summary_from_calls` to include sentiment analysis
2. Add sentiment distribution to PDF report generation
3. Remove final_loadboard_rate from displays
4. Add new section for sentiment analysis in reports
5. Update console output format for clarity

**CLI Display Format:**
```
=== METRICS SUMMARY ===
Total Calls: 150
Response Distribution:
  - Success: 45 (30%)
  - Rate too high: 60 (40%)
  - Incorrect MC: 30 (20%)
  - Fallback error: 15 (10%)

Sentiment Analysis:
  - Positive: 45 (30%)
  - Neutral: 75 (50%)
  - Negative: 30 (20%)

Top Response Reasons:
  1. Rate negotiation failed - 25 occurrences
  2. MC verification failed - 20 occurrences
  3. System timeout - 10 occurrences
```

---

### Task 5: Database Schema Updates - Phase 2
**Agent:** backend-agent
**Priority:** High
**Files to Create:**
- `migrations/versions/007_add_load_booking_fields.py`

**Files to Modify:**
- `src/infrastructure/database/models/load_model.py`

**Deliverables:**
1. Create Alembic migration for new load fields
2. Update LoadModel with new attributes
3. Add appropriate indexes for performance

---

### Task 6: Domain Layer Updates - Phase 2
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/core/domain/entities/load.py`

**Deliverables:**
1. Add new fields to Load entity
2. Update entity validation logic
3. Ensure backward compatibility

---

### Task 7: Use Case Updates - Phase 2
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/core/application/use_cases/create_load_use_case.py`
- `src/core/application/use_cases/update_load_use_case.py`

**Deliverables:**
1. Update `CreateLoadRequest` and `UpdateLoadRequest` models
2. Add new fields to use case logic
3. Implement booking status validation rules

---

### Task 8: Repository Layer Updates - Phase 2
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/infrastructure/database/postgres/load_repository.py`

**Deliverables:**
1. Update repository methods to handle new fields
2. Add query methods for booked loads
3. Implement session_id filtering capabilities

---

### Task 9: API Endpoint Updates - Phase 2
**Agent:** backend-agent
**Priority:** High
**Files to Modify:**
- `src/interfaces/api/v1/loads.py`

**Deliverables:**
1. Update request/response models with new fields
2. Add validation for new fields
3. Ensure backward compatibility for existing clients

---

### Task 10: Integration Testing - Phase 1
**Agent:** qa-agent
**Priority:** High
**Files to Create:**
- `src/tests/integration/test_metrics_sentiment.py`

**Files to Modify:**
- `src/tests/integration/test_metrics_endpoints.py`
- `src/tests/integration/test_call_metrics_endpoints.py`

**Test Scenarios:**
1. Test sentiment field validation (enum values)
2. Test metrics creation without final_loadboard_rate
3. Test response_reason field functionality
4. Test backward compatibility
5. Test CLI output with new fields

---

### Task 11: Integration Testing - Phase 2
**Agent:** qa-agent
**Priority:** High
**Files to Create:**
- `src/tests/integration/test_load_booking.py`

**Files to Modify:**
- `src/tests/integration/test_load_endpoints_simplified.py`

**Test Scenarios:**
1. Test load creation with booking fields
2. Test load update with session_id
3. Test filtering by booked status
4. Test miles and dimensions validation
5. Test num_of_pieces constraints

---

### Task 12: End-to-End Testing
**Agent:** qa-agent
**Priority:** High
**Files to Create:**
- `src/tests/e2e/test_complete_flow.py`

**Test Scenarios:**
1. Complete call flow with sentiment tracking
2. Load booking with session correlation
3. Metrics reporting with all new fields
4. CLI report generation validation

---

## Testing Strategy

### Unit Tests
- Model validation for new fields
- Repository method updates
- Use case business logic

### Integration Tests
- API endpoint validation
- Database migration verification
- Repository-database interaction

### Performance Tests
- Query performance with new indexes
- Load time with additional fields
- CLI report generation speed

### Validation Tests
- Sentiment enum validation
- UUID format for session_id
- Numeric string validation for miles
- Boolean validation for booked field

---

## Migration Strategy

### Pre-Migration Checklist
1. Backup current database
2. Test migrations in staging environment
3. Prepare rollback scripts
4. Document current data state

### Migration Execution
1. Run Phase 1 migration: `alembic upgrade head`
2. Verify Phase 1 changes
3. Deploy Phase 1 code changes
4. Run Phase 2 migration
5. Verify Phase 2 changes
6. Deploy Phase 2 code changes

### Rollback Plan
1. Keep previous migration versions
2. Prepare downgrade scripts
3. Test rollback in staging
4. Document rollback procedures

---

## Deployment Considerations

### Environment Variables
No new environment variables required

### Infrastructure Changes
- Database schema updates require migration execution
- No changes to AWS ECS configuration
- No changes to RDS configuration

### API Compatibility
- Phase 1: Breaking change (removed field) - coordinate with clients
- Phase 2: Backward compatible (optional new fields)

### Monitoring
- Monitor migration execution time
- Track API response times post-deployment
- Monitor database query performance
- Check CLI report generation success rate

---

## Risk Assessment

### High Risk
- **Migration failure**: Could cause data loss
  - Mitigation: Comprehensive backup and rollback plan

### Medium Risk
- **API breaking changes**: Phase 1 removes a field
  - Mitigation: Coordinate with all API consumers
- **Performance degradation**: New fields and indexes
  - Mitigation: Performance testing before production

### Low Risk
- **CLI compatibility**: Changes to output format
  - Mitigation: Version CLI tool appropriately

---

## Success Criteria

### Phase 1
- [ ] Metrics endpoint accepts sentiment fields
- [ ] final_loadboard_rate field removed successfully
- [ ] CLI displays sentiment analysis clearly
- [ ] All tests passing
- [ ] No performance degradation

### Phase 2
- [ ] Loads can be marked as booked
- [ ] Session correlation working
- [ ] All new fields storing correctly
- [ ] Backward compatibility maintained
- [ ] All tests passing

---

## Timeline

### Day 1
- Morning: Phase 1 database and repository updates
- Afternoon: Phase 1 API and CLI updates

### Day 2
- Morning: Phase 2 database and domain updates
- Afternoon: Phase 2 API updates

### Day 3
- Morning: Complete testing suite
- Afternoon: Documentation and deployment preparation

---

## Documentation Updates Required

1. API documentation (OpenAPI/Swagger)
2. Database schema documentation
3. CLI tool usage guide
4. Migration runbook
5. Client integration guide

---

## Agent Coordination Strategy

### Sequential Execution
1. **backend-agent** completes Phase 1 tasks (Tasks 1-4)
2. **qa-agent** validates Phase 1 (Task 10)
3. **backend-agent** completes Phase 2 tasks (Tasks 5-9)
4. **qa-agent** validates Phase 2 (Tasks 11-12)

### Communication Points
- After each migration creation
- After API endpoint updates
- Before and after testing phases
- Final validation before deployment

### Deliverable Handoffs
- Migration scripts review before execution
- API contract validation before testing
- Test results review before deployment

---

## Notes for Implementation Teams

1. **Backend Agent**: Focus on maintaining hexagonal architecture principles. Ensure all changes flow through proper layers (domain → application → infrastructure).

2. **QA Agent**: Prioritize testing the removed field to ensure no breaking dependencies exist. Validate all enum constraints thoroughly.

3. **All Agents**: Remember to create summary files (`HappyRobot_subagent_X.md`) documenting your specific implementation details and decisions.

4. **Important**: Use `.is()` method in SQLAlchemy for boolean comparisons in queries as per project guidelines.

---

## Appendix: Sample Code Snippets

### Sentiment Enum Definition
```python
from enum import Enum

class SentimentType(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"
```

### Migration Sample (Phase 1)
```python
def upgrade():
    # Remove final_loadboard_rate
    op.drop_column('call_metrics', 'final_loadboard_rate')

    # Add sentiment fields
    op.add_column('call_metrics',
        sa.Column('sentiment', sa.String(20), nullable=True))
    op.add_column('call_metrics',
        sa.Column('sentiment_reason', sa.Text(), nullable=True))

    # Rename reason to response_reason
    op.alter_column('call_metrics', 'reason',
        new_column_name='response_reason')

    # Add CHECK constraint
    op.create_check_constraint(
        'ck_call_metrics_sentiment',
        'call_metrics',
        "sentiment IN ('Positive', 'Neutral', 'Negative')"
    )
```

### Updated Request Model (Phase 1)
```python
class CallMetricsRequestModel(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=50000)
    response: str = Field(..., min_length=1, max_length=50)
    response_reason: Optional[str] = Field(None, max_length=2000)
    sentiment: Literal["Positive", "Neutral", "Negative"]
    sentiment_reason: Optional[str] = Field(None, max_length=2000)
    session_id: Optional[str] = Field(None, max_length=100)
```

---

End of Implementation Plan
