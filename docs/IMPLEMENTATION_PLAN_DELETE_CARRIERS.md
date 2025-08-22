# Implementation Plan: Delete Carriers Table and Infrastructure

## Executive Summary
This document outlines the comprehensive plan to remove the `carriers` table and all associated infrastructure from the HappyRobot FDE system. According to the project documentation, carrier authentication and verification is now handled by the HappyRobot workflow platform, making the local carriers table redundant. This removal will simplify the codebase, reduce maintenance overhead, and align with the current architectural design where carrier verification is handled externally.

## Current State Analysis

### Database Schema
- **Carriers Table**: Created in migration `001_initial_schema.py` with extensive fields for carrier information
- **Foreign Key Dependencies**:
  - Originally: `loads.booked_by_carrier_id` → `carriers.carrier_id` (removed in migration 004)
  - Originally: `calls.carrier_id` → `carriers.carrier_id` (table removed in migration 909554643437)
  - Originally: `negotiations.carrier_id` → `carriers.carrier_id` (table removed in migration 005)
- **Indexes**: Two indexes exist on `mc_number` (unique) and `dot_number`

### Code Infrastructure
The carriers functionality spans multiple layers following hexagonal architecture:

#### Files to be Deleted:
1. **Domain Layer**:
   - `src/core/domain/entities/carrier.py`
   - `src/core/ports/repositories/carrier_repository.py`

2. **Infrastructure Layer**:
   - `src/infrastructure/database/models/carrier_model.py`
   - `src/infrastructure/database/postgres/carrier_repository.py`

3. **Test Files**:
   - Tests in `src/tests/unit/test_entities.py` (Carrier entity tests)
   - Tests in `src/tests/unit/test_use_cases.py` (VerifyCarrier use case tests - commented out)

#### Files to be Modified:
1. **Import Cleanup**:
   - `src/core/domain/entities/__init__.py`
   - `src/core/ports/repositories/__init__.py`
   - `src/infrastructure/database/models/__init__.py`
   - `src/infrastructure/database/postgres/__init__.py`

2. **API Layer**:
   - `src/interfaces/api/v1/metrics.py` (removes carrier metrics functionality)

3. **Test Files**:
   - `src/tests/unit/application/test_create_load_use_case.py` (remove carrier-related mock methods)
   - `src/tests/integration/test_call_metrics_endpoints.py` (update test data if needed)

## Implementation Tasks

### Phase 1: Database Migration (Priority: HIGH)
**Agent**: backend-agent
**Task 1.1**: Create Alembic migration to drop carriers table
```bash
alembic revision --autogenerate -m "Remove carriers table and infrastructure"
```

**Migration Content**:
```python
def upgrade():
    # Drop carriers table and all associated indexes
    op.execute("DROP TABLE IF EXISTS carriers CASCADE")

def downgrade():
    # Recreate carriers table with original schema from 001_initial_schema.py
    op.create_table(
        "carriers",
        # ... full schema recreation
    )
```

### Phase 2: Remove Domain and Port Layers (Priority: HIGH)
**Agent**: backend-agent

**Task 2.1**: Delete carrier entity and repository interface
- Delete `src/core/domain/entities/carrier.py`
- Delete `src/core/ports/repositories/carrier_repository.py`
- Update `src/core/domain/entities/__init__.py` to remove Carrier import
- Update `src/core/ports/repositories/__init__.py` to remove CarrierRepository import

### Phase 3: Remove Infrastructure Layer (Priority: HIGH)
**Agent**: backend-agent

**Task 3.1**: Delete carrier model and repository implementation
- Delete `src/infrastructure/database/models/carrier_model.py`
- Delete `src/infrastructure/database/postgres/carrier_repository.py`
- Update `src/infrastructure/database/models/__init__.py` to remove CarrierModel import
- Update `src/infrastructure/database/postgres/__init__.py` to remove PostgresCarrierRepository import

### Phase 4: Update API Endpoints (Priority: HIGH)
**Agent**: backend-agent

**Task 4.1**: Remove carrier metrics from metrics endpoint
- Modify `src/interfaces/api/v1/metrics.py`:
  - Remove `PostgresCarrierRepository` import
  - Remove `carrier_metrics` field from `MetricsSummaryResponse`
  - Remove carrier metrics calculation logic in `get_metrics_summary`
  - Update response to exclude carrier-related metrics

### Phase 5: Update Tests (Priority: MEDIUM)
**Agent**: qa-agent

**Task 5.1**: Remove carrier-related tests
- Update `src/tests/unit/test_entities.py`: Remove `TestCarrier` class
- Update `src/tests/unit/test_use_cases.py`: Remove commented VerifyCarrier tests
- Update `src/tests/unit/application/test_create_load_use_case.py`: Remove `get_loads_by_carrier` method

**Task 5.2**: Verify remaining tests pass
```bash
pytest -v
pytest tests/integration/
```

### Phase 6: Clean Up References (Priority: LOW)
**Agent**: backend-agent

**Task 6.1**: Search and remove any remaining carrier references
- Remove any unused imports related to carriers
- Update documentation if needed
- Clean up any remaining MC number validation logic if not used elsewhere

## API Contract Changes

### Removed from `/api/v1/metrics/summary`:
```json
// BEFORE
{
  "carrier_metrics": {
    "repeat_callers": 0,
    "new_carriers": 0,
    "top_equipment_types": [],
    "average_mc_verification_time_ms": 0
  }
}

// AFTER
// Field completely removed from response
```

## Database Schema Changes

### Tables Affected:
- `carriers` table: **DELETED**
- No foreign key constraints remain to be dropped (already handled in previous migrations)

## Testing Strategy

### Pre-Implementation Testing:
1. Run full test suite to establish baseline: `pytest -v`
2. Document any existing test failures

### Post-Implementation Testing:
1. **Unit Tests**: Verify all domain and use case tests pass
2. **Integration Tests**: Verify API endpoints work without carrier dependencies
3. **Database Tests**: Verify migrations run successfully up and down
4. **Manual Testing**:
   - Test metrics endpoint returns data without carrier metrics
   - Verify no 500 errors due to missing carrier references

### Regression Testing:
- Load creation and management flows
- Call metrics recording
- Dashboard metrics display

## Risk Assessment

### Low Risk:
- **No Active Dependencies**: Previous migrations already removed foreign key relationships
- **External Handling**: Carrier verification is handled by HappyRobot platform
- **Clean Architecture**: Hexagonal architecture makes removal straightforward

### Mitigation Strategies:
1. **Backup Database**: Before running migration in production
2. **Rollback Plan**: Migration includes downgrade function to recreate table
3. **Staged Deployment**: Test in development environment first
4. **Monitor Logs**: Watch for any unexpected carrier references after deployment

## Deployment Checklist

### Local Development:
```bash
# 1. Create and review migration
alembic revision --autogenerate -m "Remove carriers table and infrastructure"

# 2. Test migration
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 3. Remove code files
# 4. Update imports
# 5. Run tests
pytest -v

# 6. Run linting and formatting
ruff check .
ruff format .
mypy .
```

### Production Deployment:
1. Backup production database
2. Deploy code changes via Pulumi
3. Run migration: `alembic upgrade head`
4. Monitor application logs
5. Verify metrics endpoint functionality

## Success Criteria

1. ✅ Carriers table successfully removed from database
2. ✅ All carrier-related code files deleted
3. ✅ No import errors or missing references
4. ✅ All tests pass (excluding removed carrier tests)
5. ✅ Metrics endpoint returns data without carrier metrics
6. ✅ No runtime errors in production
7. ✅ Code quality checks pass (ruff, mypy)

## Agent Assignments Summary

| Agent | Tasks | Priority |
|-------|-------|----------|
| **backend-agent** | Database migration, code removal (Phases 1-4, 6) | HIGH |
| **qa-agent** | Test updates and validation (Phase 5) | MEDIUM |
| **architect-agent** | Review and validate implementation plan | LOW |

## Timeline Estimate

- **Phase 1-3**: 1 hour (core removal)
- **Phase 4**: 30 minutes (API updates)
- **Phase 5**: 30 minutes (test updates)
- **Phase 6**: 30 minutes (cleanup)
- **Testing & Validation**: 1 hour

**Total Estimated Time**: 3.5 hours

## Notes

- The MCNumber value object (`src/core/domain/value_objects/mc_number.py`) should be retained as it may be used for validation in API requests
- No frontend changes required as per project specification
- The removal aligns with the architecture where HappyRobot platform handles carrier verification externally
