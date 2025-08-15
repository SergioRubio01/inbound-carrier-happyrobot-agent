# HappyRobot FDE API Specification

## Overview
This document defines the complete REST API specification for the HappyRobot FDE Inbound Carrier Sales automation platform. All endpoints follow RESTful principles and use JSON for request/response payloads.

## Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.happyrobot-fde.com/api/v1`

## Authentication
All endpoints (except health checks and documentation) require API key authentication.

### Authentication Methods
1. **Header**: `X-API-Key: <api-key-value>`
2. **Header**: `Authorization: ApiKey <api-key-value>`

### Exempt Endpoints
- `/health`
- `/api/v1/health`
- `/api/v1/docs`
- `/api/v1/openapi.json`
- `/api/v1/redoc`

## Common Response Codes
- `200 OK` - Successful GET or POST request
- `201 Created` - Resource successfully created
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Valid API key but insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field_errors": [
        {
          "field": "field_name",
          "message": "Field-specific error message"
        }
      ]
    },
    "request_id": "uuid-v4",
    "timestamp": "2024-08-14T10:30:00Z"
  }
}
```

## Rate Limiting
- **Default**: 100 requests per minute per API key
- **Burst**: 10 requests per second
- Headers returned:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp for rate limit reset

---

## Endpoints

### 1. FMCSA Carrier Verification

#### POST /fmcsa/verify
Verifies a carrier's Motor Carrier (MC) number against FMCSA database.

**Request Body:**
```json
{
  "mc_number": "string",
  "include_safety_score": false
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| mc_number | string | Yes | Motor Carrier number (6-8 digits) |
| include_safety_score | boolean | No | Include safety rating in response |

**Success Response (200 OK):**
```json
{
  "mc_number": "123456",
  "eligible": true,
  "carrier_info": {
    "legal_name": "ACME TRUCKING LLC",
    "dba_name": "ACME EXPRESS",
    "status": "ACTIVE",
    "entity_type": "CARRIER",
    "operating_status": "AUTHORIZED_FOR_HIRE",
    "insurance_on_file": true,
    "bipd_required": "750000",
    "bipd_on_file": "1000000",
    "cargo_required": "100000",
    "cargo_on_file": "100000",
    "bond_required": "75000",
    "bond_on_file": "75000"
  },
  "safety_score": {
    "basics_scores": {
      "unsafe_driving": 45.2,
      "hours_of_service": 32.1,
      "driver_fitness": 0,
      "controlled_substances": 0,
      "vehicle_maintenance": 28.9,
      "hazmat_compliance": null,
      "crash_indicator": 12.5
    },
    "safety_rating": "SATISFACTORY",
    "rating_date": "2023-06-15"
  },
  "verification_timestamp": "2024-08-14T10:30:00Z"
}
```

**Ineligible Response (200 OK):**
```json
{
  "mc_number": "999999",
  "eligible": false,
  "reason": "CARRIER_NOT_AUTHORIZED",
  "details": "Carrier is not authorized for hire or has inactive status",
  "verification_timestamp": "2024-08-14T10:30:00Z"
}
```

**Validation Error (422):**
```json
{
  "error": {
    "code": "INVALID_MC_NUMBER",
    "message": "MC number must be 6-8 digits",
    "details": {
      "field_errors": [
        {
          "field": "mc_number",
          "message": "Invalid format: must contain only digits"
        }
      ]
    }
  }
}
```

---

### 2. Load Search

#### POST /loads/search
Searches for available loads based on carrier preferences and equipment.

**Request Body:**
```json
{
  "equipment_type": "53-foot van",
  "origin": {
    "city": "Dallas",
    "state": "TX",
    "radius_miles": 50
  },
  "destination": {
    "city": "Los Angeles",
    "state": "CA",
    "radius_miles": 100
  },
  "pickup_date_range": {
    "start": "2024-08-15T00:00:00Z",
    "end": "2024-08-20T23:59:59Z"
  },
  "minimum_rate": 2000,
  "maximum_miles": 1500,
  "commodity_types": ["General Merchandise", "Produce"],
  "weight_range": {
    "min": 10000,
    "max": 45000
  },
  "limit": 10,
  "sort_by": "rate_per_mile_desc"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| equipment_type | string | Yes | Type of equipment (see Equipment Types) |
| origin | object | No | Origin location filter |
| destination | object | No | Destination location filter |
| pickup_date_range | object | No | Date range for pickup |
| minimum_rate | number | No | Minimum acceptable rate |
| maximum_miles | number | No | Maximum distance |
| commodity_types | array | No | Acceptable commodity types |
| weight_range | object | No | Weight range in pounds |
| limit | integer | No | Max results to return (default: 10, max: 50) |
| sort_by | string | No | Sort order (see Sort Options) |

**Equipment Types:**
- `53-foot van`
- `48-foot van`
- `Reefer`
- `Flatbed`
- `Step Deck`
- `Double Drop`
- `RGN`
- `Power Only`
- `Hotshot`
- `Box Truck`

**Sort Options:**
- `rate_desc` - Highest rate first
- `rate_asc` - Lowest rate first
- `rate_per_mile_desc` - Highest RPM first
- `miles_asc` - Shortest distance first
- `pickup_date_asc` - Earliest pickup first

**Success Response (200 OK):**
```json
{
  "search_criteria": {
    "equipment_type": "53-foot van",
    "origin": "Dallas, TX (50 mi radius)",
    "destination": "Los Angeles, CA (100 mi radius)"
  },
  "total_matches": 15,
  "returned_count": 10,
  "loads": [
    {
      "load_id": "550e8400-e29b-41d4-a716-446655440000",
      "origin": {
        "city": "Dallas",
        "state": "TX",
        "zip": "75201",
        "coordinates": {
          "lat": 32.7767,
          "lng": -96.7970
        }
      },
      "destination": {
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90001",
        "coordinates": {
          "lat": 34.0522,
          "lng": -118.2437
        }
      },
      "pickup_datetime": "2024-08-15T10:00:00Z",
      "delivery_datetime": "2024-08-18T18:00:00Z",
      "equipment_type": "53-foot van",
      "loadboard_rate": 2800.00,
      "rate_per_mile": 2.00,
      "miles": 1400,
      "weight": 42000,
      "commodity_type": "General Merchandise",
      "num_of_pieces": 1,
      "dimensions": "53ft",
      "special_requirements": ["Team drivers required", "No tarping needed"],
      "broker_info": {
        "company": "ABC Logistics",
        "contact_name": "John Smith",
        "phone": "555-123-4567",
        "email": "john@abclogistics.com"
      },
      "urgency": "NORMAL",
      "created_at": "2024-08-14T08:00:00Z"
    }
  ],
  "search_timestamp": "2024-08-14T10:30:00Z"
}
```

**No Results Response (200 OK):**
```json
{
  "search_criteria": {
    "equipment_type": "53-foot van"
  },
  "total_matches": 0,
  "returned_count": 0,
  "loads": [],
  "suggestions": {
    "expand_radius": true,
    "alternative_equipment": ["48-foot van", "Reefer"],
    "alternative_dates": true
  },
  "search_timestamp": "2024-08-14T10:30:00Z"
}
```

---

### 3. Price Negotiation

#### POST /negotiations/evaluate
Evaluates carrier's counter-offer and manages negotiation state (max 3 rounds).

**Request Body:**
```json
{
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "mc_number": "123456",
  "carrier_offer": 2900.00,
  "negotiation_round": 1,
  "context": {
    "carrier_name": "ACME Trucking",
    "previous_offers": [2800.00],
    "urgency_level": "NORMAL",
    "notes": "Carrier mentioned they are already in the area"
  }
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| load_id | uuid | Yes | ID of the load being negotiated |
| mc_number | string | Yes | Carrier's MC number |
| carrier_offer | number | Yes | Carrier's offered rate |
| negotiation_round | integer | Yes | Current round (1-3) |
| context | object | No | Additional negotiation context |

**Accepted Response (200 OK):**
```json
{
  "negotiation_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "ACCEPTED",
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "agreed_rate": 2900.00,
  "negotiation_round": 1,
  "rate_difference": 100.00,
  "percentage_over_loadboard": 3.57,
  "message": "Offer accepted. Proceeding with booking.",
  "next_steps": {
    "action": "PROCEED_TO_HANDOFF",
    "handoff_data": {
      "load_id": "550e8400-e29b-41d4-a716-446655440000",
      "agreed_rate": 2900.00,
      "carrier_mc": "123456"
    }
  },
  "timestamp": "2024-08-14T10:30:00Z"
}
```

**Counter Offer Response (200 OK):**
```json
{
  "negotiation_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "COUNTER_OFFER",
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "carrier_offer": 3200.00,
  "counter_offer": 2950.00,
  "negotiation_round": 2,
  "remaining_rounds": 1,
  "message": "I understand you need $3200, but the best I can do is $2950. This is already above our standard rate.",
  "justification": "Rate includes fuel surcharge and quick pay",
  "timestamp": "2024-08-14T10:30:00Z"
}
```

**Rejected Response (200 OK):**
```json
{
  "negotiation_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "REJECTED",
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "carrier_offer": 3500.00,
  "maximum_rate": 2950.00,
  "negotiation_round": 3,
  "message": "I'm sorry, but $3500 is beyond our budget. Our maximum for this load is $2950.",
  "alternative_action": "SEARCH_OTHER_LOADS",
  "timestamp": "2024-08-14T10:30:00Z"
}
```

**Max Rounds Exceeded (400 Bad Request):**
```json
{
  "error": {
    "code": "MAX_NEGOTIATION_ROUNDS",
    "message": "Maximum negotiation rounds (3) exceeded",
    "details": {
      "load_id": "550e8400-e29b-41d4-a716-446655440000",
      "rounds_completed": 3
    }
  }
}
```

---

### 4. Call Handoff

#### POST /calls/handoff
Initiates handoff to human sales representative with context.

**Request Body:**
```json
{
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "mc_number": "123456",
  "agreed_rate": 2900.00,
  "carrier_contact": {
    "name": "John Doe",
    "phone": "+1-555-123-4567",
    "email": "john@acmetrucking.com",
    "company": "ACME Trucking LLC"
  },
  "call_summary": {
    "duration_seconds": 180,
    "negotiation_rounds": 2,
    "initial_offer": 3200.00,
    "key_points": [
      "Carrier is 50 miles from pickup",
      "Has team drivers available",
      "Requested quick pay terms"
    ]
  },
  "handoff_reason": "DEAL_ACCEPTED",
  "priority": "HIGH",
  "preferred_rep": "rep_123"
}
```

**Success Response (200 OK):**
```json
{
  "handoff_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "READY_TO_TRANSFER",
  "assigned_rep": {
    "id": "rep_123",
    "name": "Sarah Johnson",
    "direct_line": "+1-555-987-6543",
    "availability": "AVAILABLE"
  },
  "transfer_instructions": {
    "method": "WARM_TRANSFER",
    "bridge_number": "+1-555-000-1111",
    "conference_code": "123456#",
    "estimated_wait": 10
  },
  "context_token": "eyJhbGciOiJIUzI1NiIs...",
  "message": "Transfer initiated. Connecting to Sarah Johnson.",
  "timestamp": "2024-08-14T10:30:00Z"
}
```

**Rep Unavailable Response (200 OK):**
```json
{
  "handoff_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "QUEUED",
  "queue_position": 3,
  "estimated_wait_minutes": 5,
  "callback_option": {
    "available": true,
    "message": "All representatives are busy. Would you like us to call you back?"
  },
  "alternative_actions": [
    {
      "action": "LEAVE_VOICEMAIL",
      "description": "Leave your contact information for a callback"
    },
    {
      "action": "SCHEDULE_CALLBACK",
      "description": "Schedule a specific time for us to call you"
    }
  ],
  "timestamp": "2024-08-14T10:30:00Z"
}
```

---

### 5. Call Finalization

#### POST /calls/finalize
Logs call data, extracts key information, and classifies outcome.

**Request Body:**
```json
{
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "mc_number": "123456",
  "load_id": "550e8400-e29b-41d4-a716-446655440000",
  "agreed_rate": 2900.00,
  "call_data": {
    "start_time": "2024-08-14T10:25:00Z",
    "end_time": "2024-08-14T10:30:00Z",
    "duration_seconds": 300,
    "caller_phone": "+1-555-123-4567",
    "call_recording_url": "https://recordings.happyrobot.com/call_12345.mp3"
  },
  "transcript": "Agent: Thank you for calling... [full transcript]",
  "extracted_data": {
    "carrier_name": "ACME Trucking LLC",
    "driver_name": "John Doe",
    "equipment_details": {
      "type": "53-foot van",
      "count": 2,
      "team_drivers": true
    },
    "availability": {
      "current_location": "Houston, TX",
      "available_date": "2024-08-15"
    },
    "special_requests": ["Quick pay", "Fuel advance"],
    "dat_lane_rate": 2750.00,
    "competitive_quotes": [2850.00, 2900.00]
  },
  "outcome": "ACCEPTED",
  "sentiment": "POSITIVE",
  "follow_up_required": false,
  "notes": "Carrier accepted after 2 rounds of negotiation. Very professional."
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| call_id | uuid | No | Existing call ID if updating |
| mc_number | string | Yes | Carrier's MC number |
| load_id | uuid | No | Associated load ID |
| agreed_rate | number | No | Final agreed rate if deal made |
| call_data | object | Yes | Call metadata |
| transcript | string | No | Full call transcript |
| extracted_data | object | Yes | Key data points extracted |
| outcome | string | Yes | Call outcome classification |
| sentiment | string | Yes | Sentiment analysis result |
| follow_up_required | boolean | No | Whether follow-up is needed |
| notes | string | No | Additional notes |

**Outcome Classifications:**
- `ACCEPTED` - Load booked
- `DECLINED` - Carrier declined the load
- `NEGOTIATION_FAILED` - Could not agree on rate
- `NO_EQUIPMENT` - No available equipment
- `CALLBACK_REQUESTED` - Carrier will call back
- `NOT_ELIGIBLE` - Failed MC verification
- `WRONG_LANE` - Not in carrier's lanes
- `INFORMATION_ONLY` - Just seeking information

**Sentiment Values:**
- `POSITIVE` - Friendly, cooperative
- `NEUTRAL` - Professional, matter-of-fact
- `NEGATIVE` - Frustrated, uncooperative

**Success Response (201 Created):**
```json
{
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "LOGGED",
  "data_extraction": {
    "success": true,
    "extracted_fields": 12,
    "confidence_score": 0.95
  },
  "classification": {
    "outcome": "ACCEPTED",
    "sentiment": "POSITIVE",
    "confidence": 0.92
  },
  "analytics": {
    "call_value_score": 85,
    "conversion_probability": 0.78,
    "recommended_follow_up": "Send rate confirmation"
  },
  "next_actions": [
    {
      "action": "SEND_RATE_CONFIRMATION",
      "deadline": "2024-08-14T11:00:00Z"
    },
    {
      "action": "UPDATE_LOAD_STATUS",
      "status": "BOOKED"
    }
  ],
  "message": "Call data successfully logged and processed",
  "timestamp": "2024-08-14T10:31:00Z"
}
```

---

### 6. Metrics and Analytics

#### GET /metrics/summary
Retrieves aggregated KPIs for dashboard display.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| start_date | datetime | No | Start of date range (ISO 8601) |
| end_date | datetime | No | End of date range (ISO 8601) |
| granularity | string | No | Time granularity (hour/day/week/month) |
| mc_number | string | No | Filter by specific carrier |
| include_trends | boolean | No | Include trend analysis |

**Example Request:**
```
GET /metrics/summary?start_date=2024-08-01T00:00:00Z&end_date=2024-08-14T23:59:59Z&granularity=day&include_trends=true
```

**Success Response (200 OK):**
```json
{
  "period": {
    "start": "2024-08-01T00:00:00Z",
    "end": "2024-08-14T23:59:59Z",
    "days": 14
  },
  "call_metrics": {
    "total_calls": 450,
    "unique_carriers": 287,
    "average_duration_seconds": 240,
    "peak_hour": "14:00",
    "by_outcome": {
      "accepted": 105,
      "declined": 89,
      "negotiation_failed": 76,
      "no_equipment": 45,
      "callback_requested": 35,
      "not_eligible": 28,
      "wrong_lane": 52,
      "information_only": 20
    }
  },
  "conversion_metrics": {
    "loads_booked": 105,
    "booking_rate": 23.33,
    "average_negotiation_rounds": 1.8,
    "first_offer_acceptance_rate": 45.2,
    "average_time_to_accept_minutes": 4.5
  },
  "financial_metrics": {
    "total_booked_revenue": 285750.00,
    "average_load_value": 2721.43,
    "average_agreed_rate": 2875.50,
    "average_loadboard_rate": 2750.00,
    "average_margin_percentage": 4.56,
    "rate_variance": {
      "above_loadboard": 78,
      "at_loadboard": 15,
      "below_loadboard": 12
    }
  },
  "sentiment_analysis": {
    "positive": 265,
    "neutral": 140,
    "negative": 45,
    "average_score": 0.72,
    "trend": "IMPROVING"
  },
  "carrier_metrics": {
    "repeat_callers": 67,
    "new_carriers": 220,
    "top_equipment_types": [
      {"type": "53-foot van", "count": 180},
      {"type": "Reefer", "count": 120},
      {"type": "Flatbed", "count": 95}
    ],
    "average_mc_verification_time_ms": 450
  },
  "performance_indicators": {
    "api_availability": 99.95,
    "average_response_time_ms": 125,
    "error_rate": 0.02,
    "handoff_success_rate": 96.5
  },
  "trends": {
    "daily_calls": [
      {"date": "2024-08-01", "count": 28},
      {"date": "2024-08-02", "count": 35}
    ],
    "daily_bookings": [
      {"date": "2024-08-01", "count": 6},
      {"date": "2024-08-02", "count": 9}
    ],
    "sentiment_trend": [
      {"date": "2024-08-01", "positive": 0.65},
      {"date": "2024-08-02", "positive": 0.68}
    ]
  },
  "recommendations": [
    {
      "type": "RATE_ADJUSTMENT",
      "message": "Consider increasing rates for Dallas-LA lane by 2-3%",
      "impact": "Could improve booking rate by 5%"
    },
    {
      "type": "FOLLOW_UP",
      "message": "35 carriers requested callbacks in the last 48 hours",
      "action": "Prioritize follow-up calls"
    }
  ],
  "generated_at": "2024-08-14T10:35:00Z"
}
```

---

## Webhook Events (For HappyRobot Integration)

### Event: Call Started
Sent when a new call begins.
```json
{
  "event": "call.started",
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2024-08-14T10:25:00Z",
  "caller_phone": "+1-555-123-4567",
  "agent_id": "agent_001"
}
```

### Event: MC Verified
Sent after MC verification completes.
```json
{
  "event": "mc.verified",
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "mc_number": "123456",
  "eligible": true,
  "timestamp": "2024-08-14T10:26:00Z"
}
```

### Event: Negotiation Complete
Sent when negotiation concludes.
```json
{
  "event": "negotiation.complete",
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "negotiation_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "ACCEPTED",
  "agreed_rate": 2900.00,
  "timestamp": "2024-08-14T10:29:00Z"
}
```

### Event: Call Completed
Sent when call ends.
```json
{
  "event": "call.completed",
  "call_id": "880e8400-e29b-41d4-a716-446655440003",
  "duration_seconds": 300,
  "outcome": "ACCEPTED",
  "timestamp": "2024-08-14T10:30:00Z"
}
```

---

## Best Practices for API Integration

### 1. Idempotency
- Use idempotency keys for POST requests to prevent duplicate operations
- Header: `Idempotency-Key: <unique-key>`

### 2. Pagination
For endpoints returning lists, use pagination parameters:
- `page`: Page number (1-based)
- `page_size`: Items per page (max 100)
- Response includes:
  ```json
  {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 5,
      "total_items": 95
    }
  }
  ```

### 3. Retry Strategy
- Implement exponential backoff for 5xx errors
- Maximum 3 retries
- Retry delays: 1s, 2s, 4s

### 4. Request Timeouts
- Set client timeout to 30 seconds
- Long-running operations return 202 Accepted with status URL

### 5. Versioning
- API version in URL path (/api/v1/)
- Breaking changes require new version
- Deprecation notice given 90 days in advance

### 6. Security Headers
Required request headers:
- `X-Request-ID`: Unique request identifier for tracing
- `X-Client-Version`: Client application version

Response headers:
- `X-Request-ID`: Echo of request ID
- `X-Response-Time`: Processing time in milliseconds

---

## Testing the API

### Health Check
```bash
curl -X GET http://localhost:8000/api/v1/health
```

### MC Verification Example
```bash
curl -X POST http://localhost:8000/api/v1/fmcsa/verify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-api-key" \
  -d '{
    "mc_number": "123456",
    "include_safety_score": true
  }'
```

### Load Search Example
```bash
curl -X POST http://localhost:8000/api/v1/loads/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-api-key" \
  -d '{
    "equipment_type": "53-foot van",
    "origin": {
      "city": "Dallas",
      "state": "TX",
      "radius_miles": 50
    }
  }'
```

---

## Appendix

### A. State Codes
Standard 2-letter US state codes (AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY)

### B. Equipment Type Details
| Type | Description | Typical Weight Capacity |
|------|-------------|------------------------|
| 53-foot van | Standard dry van trailer | 45,000 lbs |
| 48-foot van | Shorter dry van | 43,000 lbs |
| Reefer | Refrigerated trailer | 43,000 lbs |
| Flatbed | Open deck trailer | 48,000 lbs |
| Step Deck | Lowered deck trailer | 48,000 lbs |
| Double Drop | Extra low trailer | 45,000 lbs |
| RGN | Removable gooseneck | 70,000 lbs |
| Power Only | Tractor only, no trailer | N/A |
| Hotshot | Pickup with gooseneck | 20,000 lbs |
| Box Truck | Straight truck | 12,000 lbs |

### C. HTTP Status Code Reference
| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET or POST |
| 201 | Created | Resource created |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid API key |
| 403 | Forbidden | Valid key, no permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable | Validation error |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | Internal error |
| 502 | Bad Gateway | Upstream error |
| 503 | Unavailable | Service down |
| 504 | Gateway Timeout | Upstream timeout |
