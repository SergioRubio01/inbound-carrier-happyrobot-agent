# FMCSA API Integration Implementation Plan

## Executive Summary

This document outlines the comprehensive plan to integrate the real FMCSA WebServices API into the HappyRobot FDE platform, replacing the current database-only carrier verification with production-grade external API integration. The implementation will maintain backward compatibility with existing voice agent webhooks while adding robust error handling, caching, and fallback mechanisms.

**Business Impact**: This integration will enable real-time carrier verification using official FMCSA data, ensuring compliance and reducing risk in carrier onboarding for the Inbound Carrier Sales automation.

**Timeline**: Estimated 3-4 days for complete implementation and testing.

## Architecture Overview

The implementation follows the **Hexagonal Architecture** pattern established in the HappyRobot codebase:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│                 /api/v1/fmcsa/verify                        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│              VerifyCarrierUseCase                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│              Carrier Entity & Value Objects                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│    ┌──────────────────┐        ┌─────────────────┐         │
│    │ FMCSA API Client │        │ Cache Service    │         │
│    └──────────────────┘        └─────────────────┘         │
│    ┌──────────────────┐        ┌─────────────────┐         │
│    │ Carrier Repo     │        │ Fallback Logic   │         │
│    └──────────────────┘        └─────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Task Breakdown

### Phase 1: Infrastructure Setup (backend-agent)

#### Task 1.1: Create FMCSA Service Port Interface
**Agent**: backend-agent
**Priority**: High
**Dependencies**: None

**Files to Create**:
- `src/core/ports/services/fmcsa_service.py`

**Implementation**:
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

class IFMCSAService(ABC):
    """Port interface for FMCSA external service."""

    @abstractmethod
    async def get_carrier_by_mc_number(
        self,
        mc_number: str,
        include_safety: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Fetch carrier data from FMCSA API."""
        pass

    @abstractmethod
    async def get_carrier_safety_profile(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch carrier safety profile from FMCSA."""
        pass

    @abstractmethod
    async def verify_insurance_status(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """Verify carrier insurance status."""
        pass
```

#### Task 1.2: Implement FMCSA API Client
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Task 1.1

**Files to Create**:
- `src/infrastructure/external_apis/__init__.py`
- `src/infrastructure/external_apis/fmcsa/__init__.py`
- `src/infrastructure/external_apis/fmcsa/client.py`
- `src/infrastructure/external_apis/fmcsa/models.py`
- `src/infrastructure/external_apis/fmcsa/exceptions.py`

**Key Implementation Details**:
```python
# client.py structure
class FMCSAAPIClient(IFMCSAService):
    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session = None

    async def get_carrier_by_mc_number(self, mc_number: str, include_safety: bool = False):
        # Implementation with:
        # - API authentication headers
        # - Retry logic with exponential backoff
        # - Response parsing and validation
        # - Error handling for various HTTP status codes
```

#### Task 1.3: Implement Caching Service
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Task 1.1

**Files to Create**:
- `src/infrastructure/cache/__init__.py`
- `src/infrastructure/cache/redis_cache.py`
- `src/infrastructure/cache/memory_cache.py`
- `src/core/ports/services/cache_service.py`

**Implementation Strategy**:
- Use in-memory cache for development (TTL: 1 hour)
- Redis cache for production (TTL: 24 hours)
- Cache key pattern: `fmcsa:carrier:{mc_number}:{timestamp}`

### Phase 2: Application Layer Integration (backend-agent)

#### Task 2.1: Update VerifyCarrierUseCase
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Tasks 1.1, 1.2, 1.3

**Files to Modify**:
- `src/core/application/use_cases/verify_carrier.py`

**Key Changes**:
1. Inject `IFMCSAService` dependency
2. Implement cache-first lookup strategy
3. Add fallback to database on API failure
4. Update verification timestamp logic

```python
class VerifyCarrierUseCase:
    def __init__(
        self,
        carrier_repository: ICarrierRepository,
        fmcsa_service: IFMCSAService,
        cache_service: ICacheService
    ):
        self.carrier_repository = carrier_repository
        self.fmcsa_service = fmcsa_service
        self.cache_service = cache_service
```

#### Task 2.2: Create FMCSA Data Mapper
**Agent**: backend-agent
**Priority**: Medium
**Dependencies**: Task 2.1

**Files to Create**:
- `src/core/application/mappers/__init__.py`
- `src/core/application/mappers/fmcsa_mapper.py`

**Purpose**: Map FMCSA API response to domain entities

### Phase 3: API Layer Updates (backend-agent)

#### Task 3.1: Update API Endpoint
**Agent**: backend-agent
**Priority**: High
**Dependencies**: Tasks 2.1, 2.2

**Files to Modify**:
- `src/interfaces/api/v1/fmcsa.py`
- `src/interfaces/api/v1/dependencies/services.py` (create)

**Key Changes**:
1. Inject FMCSA service via dependency injection
2. Update response model for additional fields
3. Add detailed error responses

#### Task 3.2: Update Configuration
**Agent**: backend-agent
**Priority**: High
**Dependencies**: None

**Files to Modify**:
- `src/config/settings.py`
- `.env.example`

**Configuration to Add**:
```python
# FMCSA API Configuration
fmcsa_api_key: str = Field(alias="FMCSA_API_KEY")
fmcsa_api_base_url: str = Field(
    default="https://mobile.fmcsa.dot.gov/qc/services",
    alias="FMCSA_API_BASE_URL"
)
fmcsa_api_timeout: int = Field(default=30, alias="FMCSA_API_TIMEOUT")
fmcsa_cache_ttl: int = Field(default=86400, alias="FMCSA_CACHE_TTL")
fmcsa_enable_cache: bool = Field(default=True, alias="FMCSA_ENABLE_CACHE")
```

### Phase 4: Error Handling & Resilience (backend-agent)

#### Task 4.1: Implement Circuit Breaker Pattern
**Agent**: backend-agent
**Priority**: Medium
**Dependencies**: Task 1.2

**Files to Create**:
- `src/infrastructure/resilience/__init__.py`
- `src/infrastructure/resilience/circuit_breaker.py`

**Implementation**: Use `pybreaker` or implement custom circuit breaker

#### Task 4.2: Add Comprehensive Logging
**Agent**: backend-agent
**Priority**: Medium
**Dependencies**: All previous tasks

**Files to Modify**:
- All service and client files

**Logging Requirements**:
- API call attempts and responses
- Cache hits/misses
- Fallback activations
- Error conditions with context

### Phase 5: Testing Implementation (qa-agent)

#### Task 5.1: Unit Tests
**Agent**: qa-agent
**Priority**: High
**Dependencies**: All implementation tasks

**Files to Create**:
- `src/tests/unit/infrastructure/external_apis/test_fmcsa_client.py`
- `src/tests/unit/application/use_cases/test_verify_carrier_with_api.py`
- `src/tests/unit/infrastructure/cache/test_cache_service.py`

**Test Coverage Requirements**:
- FMCSA API client with mocked responses
- Cache service operations
- Fallback scenarios
- Error handling paths

#### Task 5.2: Integration Tests
**Agent**: qa-agent
**Priority**: High
**Dependencies**: Task 5.1

**Files to Create**:
- `src/tests/integration/test_fmcsa_integration.py`
- `src/tests/integration/test_carrier_verification_flow.py`

#### Task 5.3: Performance Tests
**Agent**: qa-agent
**Priority**: Medium
**Dependencies**: Tasks 5.1, 5.2

**Files to Create**:
- `src/tests/performance/test_fmcsa_api_performance.py`

### Phase 6: Database Migration (backend-agent)

#### Task 6.1: Update Carrier Model
**Agent**: backend-agent
**Priority**: Low
**Dependencies**: None

**Files to Modify**:
- `src/infrastructure/database/models/carrier_model.py`

**New Fields to Add**:
```python
# Additional FMCSA tracking fields
fmcsa_last_update = Column(DateTime)
fmcsa_snapshot = Column(JSON)  # Store raw FMCSA response
api_verification_status = Column(String)  # SUCCESS, FAILED, CACHED
```

#### Task 6.2: Create Migration Script
**Agent**: backend-agent
**Priority**: Low
**Dependencies**: Task 6.1

**Command**:
```bash
alembic revision --autogenerate -m "add_fmcsa_api_tracking_fields"
```

### Phase 7: Documentation & Deployment (architect-agent)

#### Task 7.1: Update API Documentation
**Agent**: architect-agent
**Priority**: Medium
**Dependencies**: All implementation tasks

**Files to Modify**:
- `docs/api/fmcsa_endpoints.md` (create)
- Update OpenAPI schema annotations

#### Task 7.2: Update Deployment Configuration
**Agent**: aws-ecs-troubleshooter
**Priority**: Low
**Dependencies**: All implementation tasks

**Files to Modify**:
- `docker-compose.yml` (add Redis service for caching)
- `infrastructure/pulumi/index.ts` (add Redis/ElastiCache configuration)

## API Contract

### Request
```http
POST /api/v1/fmcsa/verify
Content-Type: application/json
X-API-Key: {api_key}

{
  "mc_number": "123456",
  "include_safety_score": true
}
```

### Response (Success)
```json
{
  "mc_number": "123456",
  "eligible": true,
  "carrier_info": {
    "legal_name": "ABC Transport LLC",
    "dba_name": "ABC Trucking",
    "entity_type": "CARRIER",
    "operating_status": "AUTHORIZED_FOR_HIRE",
    "physical_address": "123 Main St, Dallas, TX 75201",
    "phone": "(214) 555-0100",
    "out_of_service_date": null,
    "mcs_150_date": "2024-06-15",
    "mcs_150_mileage": 250000,
    "insurance": {
      "bipd_required": 750000,
      "bipd_on_file": 1000000,
      "cargo_required": 100000,
      "cargo_on_file": 150000
    }
  },
  "safety_score": {
    "basic_scores": {
      "unsafe_driving": 45.2,
      "hours_of_service": 38.1,
      "vehicle_maintenance": 52.3,
      "controlled_substances": 0,
      "hazmat": null,
      "driver_fitness": 41.7,
      "crash_indicator": 28.9
    },
    "safety_rating": "SATISFACTORY",
    "rating_date": "2024-03-20"
  },
  "verification_source": "FMCSA_API",
  "cached": false,
  "verification_timestamp": "2024-11-15T10:30:45Z"
}
```

### Response (API Failure with Fallback)
```json
{
  "mc_number": "123456",
  "eligible": true,
  "carrier_info": {...},
  "safety_score": null,
  "verification_source": "DATABASE_FALLBACK",
  "cached": false,
  "verification_timestamp": "2024-11-15T10:30:45Z",
  "warning": "FMCSA API unavailable, using cached data from 2024-11-14"
}
```

## Error Handling Strategy

### Retry Logic
- **Initial retry**: 1 second
- **Max retries**: 3
- **Backoff multiplier**: 2
- **Max wait**: 10 seconds

### Fallback Hierarchy
1. Check in-memory/Redis cache (TTL: 24 hours)
2. Call FMCSA API with retry logic
3. On API failure, check database for recent data (< 7 days)
4. Return partial data with warning flag

### Error Codes
- `FMCSA_001`: Invalid MC number format
- `FMCSA_002`: Carrier not found in FMCSA
- `FMCSA_003`: FMCSA API timeout
- `FMCSA_004`: FMCSA API authentication failure
- `FMCSA_005`: Rate limit exceeded
- `FMCSA_006`: Service temporarily unavailable

## Testing Strategy

### Unit Test Coverage Target: 90%
- FMCSA client methods
- Cache operations
- Data mapping functions
- Error handling paths

### Integration Test Scenarios
1. Successful API call with caching
2. API failure with database fallback
3. Cache hit scenario
4. Rate limiting handling
5. Circuit breaker activation

### Performance Requirements
- API response time: < 2 seconds (p95)
- Cache response time: < 100ms
- Fallback activation: < 500ms

## Monitoring & Observability

### Metrics to Track
- FMCSA API call success rate
- Average response time
- Cache hit ratio
- Fallback activation rate
- Error rate by type

### Logging Requirements
```python
logger.info(
    "FMCSA API call",
    extra={
        "mc_number": mc_number,
        "cached": is_cached,
        "response_time": response_time,
        "source": verification_source,
        "status": "success|failure"
    }
)
```

## Security Considerations

1. **API Key Management**
   - Store FMCSA API key in environment variables
   - Never log API keys
   - Rotate keys quarterly

2. **Data Sanitization**
   - Validate MC number format before API calls
   - Sanitize all data from external API
   - Implement input validation at all layers

3. **Rate Limiting**
   - Implement client-side rate limiting
   - Track API usage per endpoint
   - Alert on approaching limits

## Dependencies to Add

Update `pyproject.toml`:
```toml
httpx = "^0.28.1"  # Already present
redis = "^5.0.0"  # For production caching
pybreaker = "^1.2.0"  # Circuit breaker pattern
tenacity = "^9.1.2"  # Already present for retry logic
```

## Migration Path

### Phase 1: Shadow Mode (Week 1)
- Deploy FMCSA integration alongside existing code
- Log both results for comparison
- No impact on production traffic

### Phase 2: Gradual Rollout (Week 2)
- 10% traffic to new implementation
- Monitor error rates and performance
- Increase to 50% if stable

### Phase 3: Full Migration (Week 3)
- 100% traffic to FMCSA API integration
- Keep database fallback active
- Monitor for 1 week before removing old code

## Risk Assessment

### High Risk
- **FMCSA API Downtime**: Mitigated by cache and database fallback
- **Rate Limiting**: Mitigated by caching and request batching

### Medium Risk
- **Data Inconsistency**: Mitigated by verification timestamps
- **Performance Degradation**: Mitigated by caching and circuit breaker

### Low Risk
- **Invalid API Responses**: Mitigated by validation and error handling

## Success Criteria

1. ✅ Real-time FMCSA data verification working
2. ✅ < 2 second response time (p95)
3. ✅ 99.9% availability with fallback
4. ✅ All existing webhooks continue working
5. ✅ Comprehensive test coverage (>90%)
6. ✅ Zero data loss during migration

## Agent Assignments Summary

### backend-agent (Primary)
- Implement FMCSA API client
- Create cache service
- Update use cases and domain logic
- Database migrations
- API endpoint updates

### qa-agent
- Comprehensive test suite
- Performance testing
- Integration testing
- Test data generation

### architect-agent
- Documentation updates
- Architecture validation
- Migration strategy oversight

### aws-ecs-troubleshooter
- Infrastructure updates for caching
- Deployment configuration
- Production monitoring setup

## Next Steps

1. **Immediate Action**: backend-agent to start with Task 1.1 and 1.2
2. **Parallel Work**: qa-agent to prepare test fixtures and mocks
3. **Review Point**: After Phase 2 completion
4. **Go-Live Decision**: After Phase 5 completion

---

**Note**: Each assigned agent must create their own `HappyRobot_subagent_Y.md` file documenting their implementation details, decisions made, and any deviations from this plan.
