# HappyRobot API Endpoints Documentation

## Overview
This document provides comprehensive documentation for all API endpoints in the HappyRobot Inbound Carrier Sales system. All endpoints are RESTful and return JSON responses.

## Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: Your deployed AWS ALB URL

## Authentication
All endpoints (except health checks and documentation) require API key authentication:
- **Header**: `X-API-Key: <your-key>` or `Authorization: ApiKey <your-key>`
- **Exempt endpoints**: `/api/v1/health`, `/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json`

## API Documentation
Interactive API documentation is available at:
- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`
- **OpenAPI Schema**: `/api/v1/openapi.json`

---

## Load Management Endpoints

### Create Load
- **Endpoint**: `POST /api/v1/loads/`
- **Description**: Create a new load in the system
- **Request Body**:
  ```json
  {
      "origin": {
          "city": "Miami",
          "state": "FL",
          "zip": "string"
      },
      "destination": {
          "city": "New York",
          "state": "NY",
          "zip": "string"
      },
      "pickup_datetime": "2025-08-23T21:57:44.672000",
      "delivery_datetime": "2025-08-24T21:57:44.672000",
      "equipment_type": "car",
      "loadboard_rate": 3000,
      "notes": "it requires help to bring outside the house",
      "weight": 500,
      "commodity_type": "fraguile",
      "booked": false,
      "dimensions": "standard",
      "num_of_pieces": 2,
      "miles": "200"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "load_id": "db97d323-1cd8-4bf6-8660-493ef21cf53b",
    "reference_number": "LD-2025-08-00009",
    "booked": false,
    "created_at": "2025-08-22T17:20:38.787892Z"
  }
  ```

### List Loads
- **Endpoint**: `GET /api/v1/loads/`
- **Description**: List all loads with optional filtering and pagination
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  |-----------|------|----------|-------------|
  | `booked` | boolean | No | Filter by booked status |
  | `equipment_type` | string | No | Filter by equipment type |
  | `start_date` | date | No | Filter by pickup date start (YYYY-MM-DD) |
  | `end_date` | date | No | Filter by pickup date end (YYYY-MM-DD) |
  | `page` | integer | No | Page number (default: 1) |
  | `limit` | integer | No | Items per page (1-100, default: 20) |
  | `sort_by` | string | No | Sort field and direction (default: created_at_desc) |

- **Response**: `200 OK`
  ```json
  {
    "loads": [
        {
            "load_id": "db97d323-1cd8-4bf6-8660-493ef21cf53b",
            "origin": "Miami, FL",
            "destination": "New York, NY",
            "pickup_datetime": "2025-08-23T21:57:44.672000",
            "delivery_datetime": "2025-08-24T21:57:44.672000",
            "equipment_type": "car",
            "loadboard_rate": 3000,
            "notes": "it requires help to bring outside the house",
            "weight": 500,
            "commodity_type": "fraguile",
            "booked": false,
            "created_at": "2025-08-22T17:20:38.787892Z",
            "dimensions": "standard",
            "num_of_pieces": 2,
            "miles": "200",
            "session_id": null
        }
    ],
    "total_count": 1,
    "page": 1,
    "limit": 20,
    "has_next": false,
    "has_previous": false
  }
  ```

### Get Load by ID
- **Endpoint**: `GET /api/v1/loads/{load_id}`
- **Description**: Get a single load by its ID
- **Path Parameters**:
  - `load_id`: UUID of the load
- **Response**: `200 OK` - Full load details

### Update Load
- **Endpoints**:
  - `PUT /api/v1/loads/{load_id}`
  - `POST /api/v1/loads/{load_id}`
  - `PATCH /api/v1/loads/{load_id}`
- **Description**: Update an existing load (partial updates supported)
- **Path Parameters**:
  - `load_id`: UUID of the load
- **Request Body**: Any fields from the create request (all optional)
- **Response**: `200 OK` - Updated load information

### Delete Load
- **Endpoint**: `DELETE /api/v1/loads/{load_id}`
- **Description**: Soft delete a load by its ID
- **Path Parameters**:
  - `load_id`: UUID of the load
- **Response**: `204 No Content`

---

## Metrics Endpoints

### Store Call Metrics
- **Endpoint**: `POST /api/v1/metrics/call`
- **Description**: Store call metrics data including transcript, response, and sentiment
- **Request Body**:
  ```json
  {
    "transcript": "Full conversation transcript...",
    "response": "Success",
    "response_reason": "Carrier accepted the offered rate",
    "sentiment": "Positive",
    "sentiment_reason": "Carrier was satisfied with the negotiation",
    "session_id": "unique-session-id"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "metrics_id": "fb09aa3d-53cd-4568-9293-f15e1206fb7c",
    "message": "Metrics stored successfully",
    "created_at": "2025-08-22T18:24:22.439089Z"
  }
  ```

### Get Metrics Summary (Deprecated)
- **Endpoint**: `GET /api/v1/metrics/summary`
- **Description**: Get aggregated KPIs for dashboard display
- **Query Parameters**:
  - `days`: Number of days to include (default: 14)
- **Response**: `200 OK` - Aggregated metrics

### Get Call Metrics Summary
- **Endpoint**: `GET /api/v1/metrics/call/summary`
- **Description**: Get aggregated statistics for call metrics
- **Query Parameters**:
  - `start_date`: Start date for filtering (ISO 8601 format)
  - `end_date`: End date for filtering (ISO 8601 format)
- **Response**: `200 OK`
  ```json
  {
    "total_calls": 150,
    "success_rate": 0.65,
    "response_distribution": {
      "Success": 97,
      "Rate too high": 35,
      "Incorrect MC": 10,
      "Fallback error": 8
    },
    "sentiment_distribution": {
      "Positive": 85,
      "Neutral": 45,
      "Negative": 20
    }
  }
  ```

### List Call Metrics
- **Endpoint**: `GET /api/v1/metrics/call`
- **Description**: Retrieve call metrics with optional date filtering
- **Query Parameters**:
  - `start_date`: Start date for filtering (ISO 8601 format)
  - `end_date`: End date for filtering (ISO 8601 format)
  - `limit`: Maximum number of results (max: 1000, default: 100)
- **Response**: `200 OK` - List of call metrics

### Get Call Metrics by ID
- **Endpoint**: `GET /api/v1/metrics/call/{metrics_id}`
- **Description**: Get specific call metrics by ID
- **Path Parameters**:
  - `metrics_id`: UUID of the metrics record
- **Response**: `200 OK` - Full metrics details

### Delete Call Metrics
- **Endpoint**: `DELETE /api/v1/metrics/call/{metrics_id}`
- **Description**: Delete specific call metrics by ID
- **Path Parameters**:
  - `metrics_id`: UUID of the metrics record
- **Response**: `204 No Content`

---

## Negotiation Endpoints

### Calculate Counter Offer
- **Endpoint**: `GET /api/v1/negotiations`
- **Description**: Calculate a simple counter-offer for negotiation (stateless)
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  |-----------|------|----------|-------------|
  | `initial_offer` | float | Yes | Initial loadboard rate |
  | `customer_offer` | float | Yes | Customer's current offer |
  | `attempt_number` | integer | Yes | Current negotiation attempt (1-3) |

- **Response**: `200 OK`
  ```json
  {
    "new_offer": 2200.00,
    "attempt_number": 2,
    "message": "We can offer $2,200 for this load"
  }
  ```

---

## Health Check Endpoints

### API Health Check
- **Endpoint**: `GET /api/v1/health`
- **Description**: API health check endpoint for load balancer
- **No Authentication Required**
- **Response**: `200 OK`
  ```json
  {
    "status": "ok"
  }
  ```

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid API key) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable Entity (validation error) |
| 429 | Too Many Requests (rate limit exceeded) |
| 500 | Internal Server Error |

---

## Rate Limiting
- Default: 100 requests per minute per API key
- Burst: Up to 200 requests allowed
- Headers returned:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets

---

## Enumerations

### Response Types
- `Success`: Call ended with successful agreement
- `Rate too high`: Carrier rejected due to rate
- `Incorrect MC`: Invalid MC number
- `Fallback error`: System error or fallback

### Sentiment Types
- `Positive`: Positive interaction
- `Neutral`: Neutral interaction
- `Negative`: Negative interaction

### Equipment Types
- `VAN`: Dry Van
- `REEFER`: Refrigerated
- `FLATBED`: Flatbed
- `STEP_DECK`: Step Deck
- `POWER_ONLY`: Power Only

### Load Sizes
- `FTL`: Full Truckload
- `LTL`: Less Than Truckload

---

## Security Headers
All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (when HTTPS is enabled)

---

## CORS Configuration
- Allowed Origins: `*` (configure specific origins in production)
- Allowed Methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`
- Allowed Headers: All headers
- Max Age: 3600 seconds

---

## Examples

### Example: Search and Book a Load
```bash
# 1. List available loads
curl -X GET "http://localhost:8000/api/v1/loads/?booked=false&equipment_type=VAN" \
  -H "X-API-Key: your-api-key"

# 2. Get specific load details
curl -X GET "http://localhost:8000/api/v1/loads/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key"

# 3. Update load as booked
curl -X PATCH "http://localhost:8000/api/v1/loads/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"booked": true}'
```

### Example: Store and Retrieve Call Metrics
```bash
# 1. Store call metrics
curl -X POST "http://localhost:8000/api/v1/metrics/call" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Call transcript...",
    "response": "Success",
    "sentiment": "Positive",
    "session_id": "call-123"
  }'

# 2. Get metrics summary
curl -X GET "http://localhost:8000/api/v1/metrics/call/summary?start_date=2024-01-01" \
  -H "X-API-Key: your-api-key"
```

---

## Support
For API issues or questions:
1. Check the interactive documentation at `/api/v1/docs` (recommended to use `Postman` app for further testing)
2. Review error messages in responses
3. Consult the main [README.md](README.md) for setup
4. Check [DEPLOYMENT.md](docs/DEPLOYMENT.md) for infrastructure issues
