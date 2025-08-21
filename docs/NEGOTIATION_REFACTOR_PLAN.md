# Negotiation System Refactoring Implementation Plan

## Executive Summary

This plan outlines the complete refactoring of the HappyRobot negotiation system, replacing the complex multi-layered architecture with a simple, stateless negotiation calculation endpoint. The refactoring will remove unnecessary database persistence, complex domain logic, and over-engineered patterns while maintaining compatibility with the HappyRobot voice agent platform.

## Current State Analysis

### Existing Complex Components to Remove
- **Use Case**: `evaluate_negotiation.py` with 236 lines of complex logic
- **Domain Entity**: `negotiation.py` with 301 lines including multiple statuses and methods
- **API Endpoint**: `negotiations.py` with 274 lines of database operations
- **Database Model**: `negotiation_model.py` with 128 lines
- **Repository Pattern**: `negotiation_repository.py` implementations (both interface and Postgres)
- **Database Migrations**: References in `001_initial_schema.py` and `909554643437_remove_calls_table_and_infrastructure.py`

### Issues with Current Implementation
1. Over-engineered with unnecessary database persistence
2. Complex state management for simple calculation
3. Multiple layers of abstraction for basic math operation
4. Violates YAGNI principle (You Aren't Gonna Need It)

## Target State

### Simple GET Endpoint
- **Endpoint**: `GET /api/v1/negotiations`
- **Parameters**:
  - `initial_offer` (float): The loadboard rate
  - `customer_offer` (float): The carrier's current offer
  - `attempt_number` (int): Current negotiation round (1-3)
- **Response**: JSON with `new_offer` and `attempt_number`
- **Logic**: Simple formula: `new_offer = initial_offer + (customer_offer - initial_offer) / 3`
- **No database storage required**

## Implementation Plan

### Phase 1: Cleanup and Deletion

#### Task 1.1: Remove API Router Registration
**Agent**: backend-agent
**Priority**: HIGH
**Files to Modify**:
- `src/interfaces/api/app.py`

**Actions**:
1. Remove import: `from src.interfaces.api.v1 import loads, metrics, negotiations`
2. Change to: `from src.interfaces.api.v1 import loads, metrics`
3. Remove router inclusion: `app.include_router(negotiations.router, prefix="/api/v1")`
4. Remove "Negotiations" from openapi_tags list

---

#### Task 1.2: Delete Negotiation Files
**Agent**: backend-agent
**Priority**: HIGH
**Files to Delete**:
- `src/interfaces/api/v1/negotiations.py`
- `src/core/application/use_cases/evaluate_negotiation.py`
- `src/core/domain/entities/negotiation.py`
- `src/core/ports/repositories/negotiation_repository.py`
- `src/infrastructure/database/postgres/negotiation_repository.py`
- `src/infrastructure/database/models/negotiation_model.py`

---

#### Task 1.3: Clean Up Import References
**Agent**: backend-agent
**Priority**: HIGH
**Files to Modify**:
- `src/core/domain/entities/__init__.py` - Remove negotiation imports
- `src/core/ports/repositories/__init__.py` - Remove INegotiationRepository import
- `src/infrastructure/database/models/__init__.py` - Remove NegotiationModel import
- `src/infrastructure/database/postgres/__init__.py` - Remove PostgresNegotiationRepository import

---

#### Task 1.4: Update Test Files
**Agent**: backend-agent
**Priority**: MEDIUM
**Files to Modify**:
- `src/tests/unit/test_use_cases.py` - Remove negotiation test imports and any negotiation tests

---

#### Task 1.5: Create Database Migration to Drop Table
**Agent**: backend-agent
**Priority**: HIGH
**Commands**:
```bash
alembic revision --autogenerate -m "remove_negotiations_table"
```

**Manual Edit Required** in generated migration:
```python
def upgrade():
    op.drop_table('negotiations')

def downgrade():
    # Recreate table structure from 001_initial_schema.py if needed
    pass
```

---

### Phase 2: Create Simple Implementation

#### Task 2.1: Create Simple Negotiations Endpoint
**Agent**: backend-agent
**Priority**: HIGH
**File to Create**: `src/interfaces/api/v1/simple_negotiations.py`

**Implementation**:
```python
"""
File: simple_negotiations.py
Description: Simple stateless negotiation calculation endpoint
Author: HappyRobot Team
Created: 2024-08-21
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])


class NegotiationResponse(BaseModel):
    """Response model for simple negotiation calculation."""

    new_offer: float
    attempt_number: int
    message: str


@router.get("", response_model=NegotiationResponse)
async def calculate_negotiation(
    initial_offer: float = Query(..., description="Initial loadboard rate"),
    customer_offer: float = Query(..., description="Customer's current offer"),
    attempt_number: int = Query(..., ge=1, le=3, description="Current negotiation attempt (1-3)"),
) -> NegotiationResponse:
    """
    Calculate a simple counter-offer for negotiation.

    This endpoint provides a stateless calculation for price negotiation,
    moving 1/3 of the way from the initial offer toward the customer's offer.
    """
    # Simple negotiation formula: move 1/3 toward customer offer
    new_offer = initial_offer + (customer_offer - initial_offer) / 3

    # Round to 2 decimal places for currency
    new_offer = round(new_offer, 2)

    # Increment attempt number for next round
    next_attempt = min(attempt_number + 1, 3)

    # Generate appropriate message based on attempt
    if attempt_number >= 3:
        message = "Final offer - no further negotiation available"
    else:
        message = f"Counter-offer for round {attempt_number}"

    return NegotiationResponse(
        new_offer=new_offer,
        attempt_number=next_attempt,
        message=message
    )
```

---

#### Task 2.2: Register New Simple Router
**Agent**: backend-agent
**Priority**: HIGH
**File to Modify**: `src/interfaces/api/app.py`

**Actions**:
1. Add import: `from src.interfaces.api.v1 import loads, metrics, simple_negotiations`
2. Add router: `app.include_router(simple_negotiations.router, prefix="/api/v1")`

---

#### Task 2.3: Update __init__.py
**Agent**: backend-agent
**Priority**: LOW
**File to Modify**: `src/interfaces/api/v1/__init__.py`

**Actions**:
1. Add to imports: `from . import simple_negotiations`
2. Update __all__: `__all__ = ["loads", "simple_negotiations"]`

---

### Phase 3: Quality Assurance

#### Task 3.1: Code Quality Checks
**Agent**: qa-agent
**Priority**: HIGH
**Commands to Run**:
```bash
# Check for any remaining TODOs or FIXMEs
rg "TODO|FIXME" src/

# Run linting
ruff check src/

# Run formatting
ruff format src/

# Run type checking
mypy src/
```

**Expected Outcomes**:
- No TODO/FIXME comments in src/ directory
- All linting errors resolved
- Code properly formatted
- Type checking passes

---

#### Task 3.2: Test Simple Endpoint
**Agent**: qa-agent
**Priority**: HIGH
**Commands**:
```bash
# Start the application
docker compose up --build

# Test the new endpoint
curl -X GET "http://localhost:8000/api/v1/negotiations?initial_offer=1000&customer_offer=1300&attempt_number=1" \
  -H "X-API-Key: dev-local-api-key"
```

**Expected Response**:
```json
{
  "new_offer": 1100.00,
  "attempt_number": 2,
  "message": "Counter-offer for round 1"
}
```

---

#### Task 3.3: Verify Database Migration
**Agent**: backend-agent
**Priority**: HIGH
**Commands**:
```bash
# Apply migration
alembic upgrade head

# Verify table is dropped
docker exec -it happyrobot-postgres psql -U happyrobot -d happyrobot -c "\dt"
```

**Expected**: negotiations table should not appear in the list

---

#### Task 3.4: Integration Test
**Agent**: qa-agent
**Priority**: MEDIUM
**File to Create**: `src/tests/integration/test_simple_negotiations.py`

```python
"""Test simple negotiations endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_simple_negotiation_calculation(test_client: AsyncClient):
    """Test basic negotiation calculation."""
    response = await test_client.get(
        "/api/v1/negotiations",
        params={
            "initial_offer": 1000,
            "customer_offer": 1600,
            "attempt_number": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_offer"] == 1200.00
    assert data["attempt_number"] == 2
    assert "round 1" in data["message"]


@pytest.mark.asyncio
async def test_final_negotiation_round(test_client: AsyncClient):
    """Test final round behavior."""
    response = await test_client.get(
        "/api/v1/negotiations",
        params={
            "initial_offer": 1000,
            "customer_offer": 1600,
            "attempt_number": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["attempt_number"] == 3
    assert "Final offer" in data["message"]
```

---

### Phase 4: Documentation and Handoff

#### Task 4.1: Create API Documentation
**Agent**: backend-agent
**Priority**: LOW
**Actions**:
- The FastAPI automatic documentation at `/api/v1/docs` will be updated automatically
- Verify the endpoint appears correctly in Swagger UI

---

#### Task 4.2: Create Summary Report
**Agent**: qa-agent
**Priority**: LOW
**File to Create**: `HappyRobot_subagent_1.md`

**Content**: Summary of all changes made, verification results, and any issues found

---

## Execution Order and Dependencies

1. **Phase 1** (Cleanup) - Tasks 1.1-1.5 must be completed first
   - Can be done in parallel: 1.1, 1.2, 1.3, 1.4
   - Task 1.5 depends on 1.2 completion

2. **Phase 2** (Implementation) - Depends on Phase 1
   - Task 2.1 first
   - Tasks 2.2 and 2.3 depend on 2.1

3. **Phase 3** (QA) - Depends on Phase 2
   - Tasks 3.1-3.4 can run in parallel after Phase 2

4. **Phase 4** (Documentation) - Final phase after all testing

## Risk Assessment

### Low Risks
- Simple calculation logic has minimal failure points
- No database dependencies reduce complexity
- Stateless design eliminates session management issues

### Medium Risks
- Existing integrations might expect the old POST endpoint
- Migration rollback strategy if issues arise

### Mitigation Strategies
1. Keep old endpoint code in version control for emergency rollback
2. Test thoroughly with HappyRobot voice agent platform
3. Communicate endpoint change to integration partners

## Success Criteria

1. ✅ All old negotiation code removed
2. ✅ New simple GET endpoint functional
3. ✅ No TODO/FIXME comments remain
4. ✅ All linting and type checking passes
5. ✅ Database migration successful
6. ✅ Integration tests pass
7. ✅ API documentation updated

## Timeline Estimate

- **Phase 1**: 30 minutes
- **Phase 2**: 20 minutes
- **Phase 3**: 30 minutes
- **Phase 4**: 10 minutes
- **Total**: ~1.5 hours

## Agent Assignments Summary

- **backend-agent**: Tasks 1.1-1.5, 2.1-2.3, 3.3, 4.1 (Primary implementation)
- **qa-agent**: Tasks 3.1, 3.2, 3.4, 4.2 (Quality assurance and testing)
- **architect-agent**: Review and validation of overall plan (optional)

## Notes for Agents

Each agent assigned to tasks should:
1. Create their own `HappyRobot_subagent_X.md` summary file
2. Report any blockers immediately
3. Verify changes don't break existing functionality
4. Follow the hexagonal architecture patterns for any new code
5. Ensure compliance with CLAUDE.md guidelines

---

**Plan Created**: 2024-08-21
**Author**: Implementation Planning Agent
**Status**: Ready for Execution
