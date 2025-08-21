# Metrics System Simplification - Implementation Plan

## Executive Summary
This document outlines a 3-phase implementation plan to simplify the HappyRobot FDE metrics system. The current complex metrics endpoint will be replaced with a streamlined solution that stores essential call data (transcript, response, reason, final_loadboard_rate) and provides simple retrieval with PDF report generation capabilities.

**Timeline**: 3-4 days
**Risk Level**: Low
**Business Impact**: Improved data collection and reporting capabilities

---

## Phase 1: Backend Simplification (Backend Agent)
**Duration**: 1-2 days
**Agent Assignment**: backend-agent (subagent 2)

### 1.1 Database Model Creation
**Task**: Create new CallMetrics model
**Files to Create**:
- `src/infrastructure/database/models/call_metrics_model.py`

**Model Structure**:
```python
class CallMetricsModel(Base, TimestampMixin):
    __tablename__ = "call_metrics"

    # Primary Key
    metrics_id: UUID (primary key)

    # Core Fields
    transcript: Text (nullable=False)
    response: String(50) (nullable=False)  # ACCEPTED, REJECTED, etc.
    reason: Text (nullable=True)
    final_loadboard_rate: NUMERIC(10, 2) (nullable=True)

    # Metadata
    session_id: String(100) (index=True, nullable=True)
    created_at: TIMESTAMP (auto-generated)
```

### 1.2 Database Migration
**Task**: Create Alembic migration
**Command**: `alembic revision --autogenerate -m "add_call_metrics_table"`
**Files to Create**:
- `migrations/versions/XXX_add_call_metrics_table.py`

### 1.3 Repository Implementation
**Task**: Create repository for CallMetrics
**Files to Create**:
- `src/infrastructure/database/postgres/call_metrics_repository.py`

**Key Methods**:
- `create_metrics(transcript, response, reason, final_loadboard_rate)`
- `get_metrics(start_date=None, end_date=None, limit=100)`
- `get_metrics_by_id(metrics_id)`
- `get_metrics_summary(start_date, end_date)`

### 1.4 Update Module Exports
**Files to Modify**:
- `src/infrastructure/database/models/__init__.py` - Add CallMetricsModel
- `src/infrastructure/database/postgres/__init__.py` - Add PostgresCallMetricsRepository

### 1.5 Implement POST Endpoint
**Task**: Simplify metrics.py to include new POST endpoint
**Files to Modify**:
- `src/interfaces/api/v1/metrics.py`

**New Endpoint**:
```python
@router.post("/call", status_code=201)
async def create_call_metrics(
    transcript: str,
    response: str,
    reason: Optional[str] = None,
    final_loadboard_rate: Optional[float] = None,
    session: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Store call metrics data."""
```

### Testing Requirements:
- Unit tests for CallMetricsModel
- Integration tests for repository methods
- API endpoint tests with various payloads

---

## Phase 2: Data Retrieval Implementation (Backend Agent)
**Duration**: 0.5-1 day
**Agent Assignment**: backend-agent (subagent 3)
**Dependencies**: Phase 1 must be complete

### 2.1 GET Endpoint Implementation
**Task**: Add GET endpoint for metrics retrieval
**Files to Modify**:
- `src/interfaces/api/v1/metrics.py`

**New Endpoints**:
```python
@router.get("/call")
async def get_call_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_database_session)
) -> List[CallMetricsResponseModel]

@router.get("/call/{metrics_id}")
async def get_call_metrics_by_id(
    metrics_id: UUID,
    session: AsyncSession = Depends(get_database_session)
) -> CallMetricsResponseModel
```

### 2.2 Response Models
**Task**: Create Pydantic response models
**Location**: Within `src/interfaces/api/v1/metrics.py`

```python
class CallMetricsResponseModel(BaseModel):
    metrics_id: UUID
    transcript: str
    response: str
    reason: Optional[str]
    final_loadboard_rate: Optional[float]
    created_at: datetime

class CallMetricsListResponse(BaseModel):
    metrics: List[CallMetricsResponseModel]
    total_count: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
```

### 2.3 Aggregation Endpoint
**Task**: Add summary statistics endpoint
**New Endpoint**:
```python
@router.get("/call/summary")
async def get_metrics_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_database_session)
) -> MetricsSummaryResponse
```

### Testing Requirements:
- Test filtering by date range
- Test pagination limits
- Test summary calculations
- Test error handling for invalid IDs

---

## Phase 3: CLI Tool with PDF Generation (Backend Agent)
**Duration**: 1 day
**Agent Assignment**: backend-agent (subagent 4)
**Dependencies**: Phase 2 must be complete

### 3.1 CLI Tool Creation
**Task**: Create CLI tool for metrics fetching and PDF generation
**Files to Create**:
- `src/interfaces/cli.py`

### 3.2 Install PDF Dependencies
**Task**: Add PDF generation library
**Files to Modify**:
- `pyproject.toml` - Add `reportlab>=4.0.0` to dependencies

### 3.3 CLI Implementation
**Structure**:
```python
import argparse
from datetime import datetime, timedelta
import httpx
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def fetch_metrics(api_url, api_key, start_date=None, end_date=None):
    """Fetch metrics from API."""

def generate_pdf_report(metrics_data, output_file="metrics_report.pdf"):
    """Generate PDF report from metrics data."""

def main():
    parser = argparse.ArgumentParser(description="HappyRobot Metrics CLI")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="metrics_report.pdf", help="Output PDF file")
    parser.add_argument("--format", choices=["pdf", "json"], default="pdf")
```

### 3.4 PDF Report Sections
**Report Structure**:
1. **Header**: Report title, date range, generation timestamp
2. **Summary Statistics**:
   - Total calls processed
   - Acceptance rate
   - Average final loadboard rate
   - Response distribution (pie chart)
3. **Detailed Metrics Table**:
   - Timestamp
   - Response
   - Reason
   - Final Loadboard Rate
4. **Top Rejection Reasons**: Grouped and counted

### 3.5 CLI Commands
**Usage Examples**:
```bash
# Generate PDF report for last 7 days
python -m src.interfaces.cli --api-key YOUR_KEY

# Generate report for specific date range
python -m src.interfaces.cli --api-key YOUR_KEY --start-date 2024-01-01 --end-date 2024-01-31

# Output as JSON instead of PDF
python -m src.interfaces.cli --api-key YOUR_KEY --format json

# Custom output file
python -m src.interfaces.cli --api-key YOUR_KEY --output january_report.pdf
```

### Testing Requirements:
- Test CLI argument parsing
- Test API connection and authentication
- Test PDF generation with various data sets
- Test error handling for API failures

---

## Migration Strategy

### Deprecation Plan
1. Keep existing `/metrics/summary` endpoint temporarily
2. Add deprecation warning header: `X-Deprecated: Use /api/v1/metrics/call instead`
3. Remove after 30 days or once all clients migrate

### Data Migration
- Existing negotiation data can optionally be migrated to call_metrics table
- Migration script can extract relevant fields from negotiations table

---

## Risk Assessment

### Low Risk Items
- New table creation (no impact on existing data)
- Simple data model (minimal complexity)
- CLI tool is standalone

### Medium Risk Items
- API endpoint changes (requires client updates)
- PDF generation library dependencies

### Mitigation Strategies
- Maintain backward compatibility temporarily
- Comprehensive testing before deployment
- Feature flag for gradual rollout

---

## Success Criteria

1. **Phase 1 Success**:
   - CallMetrics model created and migrated
   - POST endpoint accepts and stores data
   - All tests passing

2. **Phase 2 Success**:
   - GET endpoints return correct data
   - Filtering and pagination work correctly
   - Summary statistics are accurate

3. **Phase 3 Success**:
   - CLI tool generates valid PDF reports
   - Reports contain all required sections
   - CLI handles errors gracefully

---

## Coordination Notes

### Inter-Agent Communication
- Each agent must create `HappyRobot_subagent_X.md` summary file upon completion
- Agents should check for completion of dependent phases before starting
- Use git branches: `feat/metrics-phase-1`, `feat/metrics-phase-2`, `feat/metrics-phase-3`

### Testing Strategy
Each phase must include:
1. Unit tests with >80% coverage
2. Integration tests for API endpoints
3. Manual testing checklist
4. Performance testing for large datasets

### Documentation Updates
- Update API documentation with new endpoints
- Create CLI usage guide
- Update CLAUDE.md with new metrics system information

---

## Appendix: API Contract

### POST /api/v1/metrics/call
**Request Body**:
```json
{
  "transcript": "Full conversation transcript...",
  "response": "ACCEPTED",
  "reason": "Rate was within acceptable range",
  "final_loadboard_rate": 2500.00
}
```

**Response (201 Created)**:
```json
{
  "metrics_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Metrics stored successfully",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/metrics/call
**Query Parameters**:
- `start_date` (optional): ISO 8601 datetime
- `end_date` (optional): ISO 8601 datetime
- `limit` (optional): Max results (default 100, max 1000)

**Response (200 OK)**:
```json
{
  "metrics": [
    {
      "metrics_id": "550e8400-e29b-41d4-a716-446655440000",
      "transcript": "...",
      "response": "ACCEPTED",
      "reason": "...",
      "final_loadboard_rate": 2500.00,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z"
}
```

### GET /api/v1/metrics/call/summary
**Response (200 OK)**:
```json
{
  "total_calls": 500,
  "acceptance_rate": 0.65,
  "average_final_rate": 2450.50,
  "response_distribution": {
    "ACCEPTED": 325,
    "REJECTED": 150,
    "ABANDONED": 25
  },
  "top_rejection_reasons": [
    {"reason": "Rate too high", "count": 75},
    {"reason": "Equipment mismatch", "count": 50},
    {"reason": "Route not preferred", "count": 25}
  ],
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  }
}
```

---

## Conclusion

This implementation plan provides a clear path to simplifying the metrics system while maintaining functionality and adding new capabilities. The phased approach minimizes risk and allows for incremental validation of each component.

**Next Steps**:
1. Review and approve this plan
2. Assign backend-agent to begin Phase 1
3. Set up monitoring for migration progress
4. Schedule stakeholder review after Phase 2 completion
