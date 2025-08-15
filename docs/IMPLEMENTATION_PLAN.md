# FDE Technical Challenge: Implementation Plan

## Task Checklist with Agent Assignments

### Phase 1: Architecture and Database Foundation
- [ ] **Design API contracts and validate hexagonal architecture** (architect-agent)
  - Define complete OpenAPI specification for all endpoints
  - Validate domain entities and value objects design
  - Create sequence diagrams for agent workflow
  - Files: Create `docs/api-specification.yaml`, update existing architecture docs

- [ ] **Create database models and SQLAlchemy entities** (backend-agent)
  - Implement Load, Call, Negotiation, and Carrier models in `src/infrastructure/database/models/`
  - Create repository interfaces in `src/core/ports/repositories/`
  - Implement PostgreSQL repositories in `src/infrastructure/database/postgres/`
  - Files: `load_model.py`, `call_model.py`, `negotiation_model.py`, `carrier_model.py`

- [ ] **Generate and apply database migrations** (backend-agent)
  - Create initial migration for all tables using Alembic
  - Add indexes for performance (MC number, load status, created_at)
  - Seed example loads data
  - Files: `migrations/versions/001_initial_schema.py`

### Phase 2: Core API Implementation
- [ ] **Implement FMCSA verification endpoint** (backend-agent)
  - Create use case in `src/core/application/use_cases/verify_carrier.py`
  - Implement mock FMCSA service for POC in `src/infrastructure/services/`
  - Add endpoint logic in `src/interfaces/api/v1/fmcsa.py`
  - Include proper error handling and validation

- [ ] **Implement load search functionality** (backend-agent)
  - Create load search use case with filtering logic
  - Implement repository methods for load queries
  - Add endpoint in `src/interfaces/api/v1/loads.py`
  - Support equipment type, origin, date range filters

- [ ] **Build negotiation evaluation system** (backend-agent)
  - Create negotiation state management (max 3 rounds)
  - Implement pricing logic and thresholds
  - Add stateful tracking in database
  - Update `src/interfaces/api/v1/negotiations.py`

- [ ] **Implement call finalization and handoff** (backend-agent)
  - Create call logging and extraction logic
  - Implement sentiment analysis (simple rule-based for POC)
  - Add handoff metadata generation
  - Complete `src/interfaces/api/v1/calls.py`

- [ ] **Add metrics aggregation endpoint** (backend-agent)
  - Create aggregation queries for KPIs
  - Implement caching strategy for performance
  - Add endpoint in `src/interfaces/api/v1/metrics.py`
  - Return booking rate, sentiment breakdown, averages

### Phase 3: Security and Middleware
- [ ] **Configure API key authentication middleware** (backend-agent)
  - Enhance existing auth middleware in `src/interfaces/api/v1/middleware/auth_middleware.py`
  - Add API key validation from environment/headers
  - Configure exempt endpoints list
  - Add rate limiting per API key

### Phase 4: Frontend Dashboard
- [ ] **Update Next.js dashboard with metrics display** (frontend-agent)
  - Modify `web_client/src/app/page.tsx` to display KPIs
  - Add API integration using existing `useApi` hook
  - Create metric cards for: total calls, booking rate, sentiment
  - Add call agent button that triggers test webhook
  - Use existing shadcn/ui components for consistency

### Phase 5: Containerization and Local Development
- [ ] **Finalize Docker configuration** (backend-agent)
  - Update `Dockerfile.api` with all dependencies
  - Ensure `docker-compose.yml` includes pgAdmin configuration
  - Add health checks for all services
  - Configure proper networking between containers

- [ ] **Create docker entrypoint scripts** (backend-agent)
  - Add migration runner in `scripts/docker-entrypoint.sh`
  - Include database initialization checks
  - Add seed data loading for development

### Phase 6: AWS Infrastructure Setup
- [ ] **Configure Pulumi infrastructure as code** (cloud-agent)
  - Set up VPC and networking in `infrastructure/pulumi/components/network.ts`
  - Configure RDS PostgreSQL in `infrastructure/pulumi/components/database.ts`
  - Set up ECS cluster and services in `infrastructure/pulumi/components/compute.ts`
  - Configure ALB with HTTPS in `infrastructure/pulumi/components/loadbalancer.ts`

- [ ] **Set up ECR repositories and build pipeline** (cloud-agent)
  - Create ECR repositories for API and frontend
  - Configure GitHub Actions or similar for CI/CD
  - Add build and push scripts
  - Set up environment-specific configurations

- [ ] **Configure secrets and environment management** (cloud-agent)
  - Set up AWS Secrets Manager for API keys and DB credentials
  - Configure ECS task definitions with proper env vars
  - Add Parameter Store for non-sensitive config
  - Document deployment variables

### Phase 7: Testing and Quality Assurance
- [ ] **Write comprehensive unit tests** (qa-agent)
  - Test all use cases and domain logic
  - Add repository tests with mocked database
  - Test API endpoints with FastAPI TestClient
  - Achieve minimum 80% code coverage

- [ ] **Create integration tests** (qa-agent)
  - Test full API workflow from MC verification to handoff
  - Add database integration tests
  - Test error scenarios and edge cases
  - Validate API authentication

- [ ] **Perform code cleanup and optimization** (qa-agent)
  - Run linting (ruff) and formatting
  - Check type hints with mypy
  - Remove unused imports and dead code
  - Optimize database queries

### Phase 8: Documentation and Delivery
- [ ] **Create HappyRobot configuration guide** (general-purpose-agent)
  - Document exact webhook URLs and payloads
  - Create step-by-step agent setup instructions
  - Include example conversation flows
  - Add troubleshooting section

- [ ] **Prepare deployment documentation** (general-purpose-agent)
  - Create deployment runbook
  - Document environment variables
  - Add monitoring and logging setup
  - Include rollback procedures

- [ ] **Create demo materials** (general-purpose-agent)
  - Prepare demo script with talking points
  - Create test data for demonstration
  - Document common scenarios
  - Prepare backup plan for demo issues

## Agent Responsibilities Summary

### architect-agent
- System design and architecture validation
- API contract definition
- Database schema design review
- Integration patterns and best practices

### backend-agent
- FastAPI endpoint implementation
- Database models and migrations
- Business logic and use cases
- Docker configuration
- Core POC functionality

### frontend-agent
- Single-page dashboard update
- API integration for metrics
- UI components and styling
- Call agent button implementation

### cloud-agent
- AWS infrastructure setup with Pulumi
- ECS/Fargate configuration
- RDS database provisioning
- CI/CD pipeline setup
- Security and networking

### qa-agent
- Unit and integration testing
- Code quality checks
- Performance validation
- Security review
- Final cleanup

### general-purpose-agent
- Documentation creation
- HappyRobot platform configuration
- Demo preparation
- Knowledge transfer materials

## Execution Order
1. Architecture and Database Foundation (architect + backend)
2. Core API Implementation (backend)
3. Security and Middleware (backend)
4. Frontend Dashboard (frontend) - can run in parallel with API work
5. Containerization (backend)
6. AWS Infrastructure (cloud) - can start early in parallel
7. Testing and QA (qa) - ongoing throughout development
8. Documentation and Delivery (general-purpose)

## Critical Path Dependencies
- Database models must be complete before API implementation
- API endpoints must be functional before frontend integration
- Docker setup must be complete before AWS deployment
- All testing must pass before final delivery

---

## 1. Executive Summary for Acme Logistics

**Project:** Automated Inbound Carrier Load Booking Agent

**Objective:** To streamline the inbound carrier sales process by deploying an AI-powered agent on the HappyRobot platform. This agent will handle initial carrier calls, verify eligibility, match carriers with available loads, conduct price negotiations, and escalate to a human sales representative only when a deal is confirmed. This will increase efficiency, reduce manual workload, and allow sales staff to focus on high-value conversations.

**Key Features:**
- **24/7 Availability:** The agent can answer carrier calls at any time.
- **Instant Carrier Verification:** Authenticates carrier MC numbers against the FMCSA database in real-time.
- **Automated Load Matching:** Searches and proposes relevant loads based on carrier equipment and availability.
- **Automated Negotiation:** Handles up to three rounds of rate negotiation within predefined limits.
- **Seamless Handoff:** Transfers the call and all relevant context to a sales representative upon successful negotiation.
- **Data Extraction & Analytics:** Captures key data points from every call, classifies call outcomes, and analyzes carrier sentiment to provide actionable insights via a performance dashboard.

**Security & Compliance:** All API communications are secured with API Key authentication. The system is designed for deployment on AWS, ensuring scalability and reliability.

## 2. Technical Implementation Details

### 2.1. System Architecture
The solution consists of three main components:
1.  **HappyRobot Agent:** The conversational AI configured in the HappyRobot platform.
2.  **Backend API:** A FastAPI application that serves as the "brain" for the agent, handling all business logic.
3.  **Database:** A PostgreSQL database to store load information and call data.

The architecture is simplified for this POC to focus on core functionality, using a RESTful API and a relational database, without Redis, WebSockets, or separate backup services.

### 2.2. Database Schema and Models
The database schema will be defined and managed using SQLAlchemy models and migrated using Alembic. The raw SQL below is provided for reference and for quick manual setup in a tool like pgAdmin.

#### SQLAlchemy Models
Models for `Load` and `Call` will be created in `src/infrastructure/database/models/`. These will map directly to the tables below.

#### `loads` table
This table will be pre-populated with available loads.

```sql
CREATE TABLE IF NOT EXISTS loads (
    load_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    pickup_datetime TIMESTAMPTZ NOT NULL,
    delivery_datetime TIMESTAMPTZ NOT NULL,
    equipment_type VARCHAR(100) NOT NULL,
    loadboard_rate NUMERIC(10, 2) NOT NULL,
    notes TEXT,
    weight INTEGER,
    commodity_type VARCHAR(100),
    num_of_pieces INTEGER,
    miles INTEGER,
    dimensions VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Example data
INSERT INTO loads (origin, destination, pickup_datetime, delivery_datetime, equipment_type, loadboard_rate, notes, weight, commodity_type, num_of_pieces, miles, dimensions) VALUES
('Dallas, TX', 'Los Angeles, CA', '2024-08-15 10:00:00Z', '2024-08-18 18:00:00Z', '53-foot van', 2800.00, 'Team drivers required', 42000, 'General Merchandise', 1, 1400, '53ft'),
('Chicago, IL', 'Atlanta, GA', '2024-08-16 14:00:00Z', '2024-08-17 22:00:00Z', 'Reefer', 2200.00, 'Temp at 34F', 38000, 'Produce', 20, 720, '53ft');
```

#### `calls` table
This table will store data extracted from each call.
```sql
CREATE TABLE IF NOT EXISTS calls (
    call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mc_number VARCHAR(20),
    load_id UUID REFERENCES loads(load_id),
    agreed_rate NUMERIC(10, 2),
    call_outcome VARCHAR(50) NOT NULL, -- e.g., 'accepted', 'declined', 'negotiation_failed'
    carrier_sentiment VARCHAR(50) NOT NULL, -- e.g., 'positive', 'neutral', 'negative'
    call_transcript TEXT,
    extracted_data JSONB, -- Store other relevant data like contact info
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.3. API Endpoints
All endpoints are prefixed with `/api/v1` and require an `X-API-Key` header.

---

#### 1. Verify MC Number
- **Endpoint:** `POST /fmcsa/verify`
- **Description:** Verifies a carrier's Motor Carrier (MC) number. For the POC, this can be a mock that checks against a predefined list.
- **Request Body:**
  ```json
  {
    "mc_number": "123456"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "mc_number": "123456",
    "eligible": true,
    "details": "Carrier is active and authorized."
  }
  ```
- **Failure Response (200 OK):**
  ```json
  {
    "mc_number": "999999",
    "eligible": false,
    "details": "Carrier is not authorized for hire."
  }
  ```

---

#### 2. Search for Loads
- **Endpoint:** `POST /loads/search`
- **Description:** Searches for available loads based on criteria gathered from the carrier.
- **Request Body:**
  ```json
  {
    "equipment_type": "53-foot van",
    "origin_city": "Dallas",
    "origin_state": "TX"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "loads": [
      {
        "load_id": "a1b2c3d4-...",
        "origin": "Dallas, TX",
        "destination": "Los Angeles, CA",
        "pickup_datetime": "2024-08-15T10:00:00Z",
        "loadboard_rate": 2800.00,
        "equipment_type": "53-foot van"
      }
    ]
  }
  ```

---

#### 3. Evaluate Counter Offer
- **Endpoint:** `POST /negotiations/evaluate`
- **Description:** Evaluates a carrier's counter-offer for a load. The logic will accept if the offer is within a certain threshold (e.g., <= 10% above `loadboard_rate`). This is the only stateful endpoint, tracking negotiation rounds.
- **Request Body:**
  ```json
  {
    "load_id": "a1b2c3d4-...",
    "carrier_offer": 2900.00,
    "negotiation_round": 1
  }
  ```
- **Success Response (200 OK):**
  - If accepted:
    ```json
    {
      "status": "accepted",
      "agreed_rate": 2900.00
    }
    ```
  - If countered:
    ```json
    {
      "status": "counter_offer",
      "new_offer": 2850.00
    }
    ```
  - If rejected:
    ```json
    {
      "status": "rejected",
      "reason": "Offer too high. Maximum is $2850."
    }
    ```

---

#### 4. Finalize and Log Call
- **Endpoint:** `POST /calls/finalize`
- **Description:** Logs the final details of the call, including outcome and extracted data.
- **Request Body:**
  ```json
  {
    "mc_number": "123456",
    "load_id": "a1b2c3d4-...",
    "agreed_rate": 2900.00,
    "outcome": "accepted",
    "sentiment": "positive",
    "transcript": "...",
    "extracted_data": {
      "carrier_name": "John Doe"
    }
  }
  ```
- **Success Response (201 Created):**
  ```json
  {
    "call_id": "e5f6g7h8-...",
    "message": "Call details logged successfully."
  }
  ```

---

#### 5. Get Dashboard Metrics
- **Endpoint:** `GET /metrics/summary`
- **Description:** Retrieves aggregated metrics for the dashboard.
- **Success Response (200 OK):**
  ```json
  {
    "total_calls": 150,
    "loads_booked": 35,
    "booking_rate_percent": 23.3,
    "average_negotiation_rounds": 1.8,
    "sentiment_breakdown": {
      "positive": 95,
      "neutral": 40,
      "negative": 15
    }
  }
  ```

## 3. HappyRobot Platform Configuration

1.  **Create Agent:** "Inbound Carrier Sales" with Voice capability and a Web Call Trigger.
2.  **Step 1: Get MC Number:** Use a "Get Response" node to ask for the MC number and store it in a variable (e.g., `mc_number`).
3.  **Step 2: Verify MC (HTTP Node):**
    - URL: `YOUR_API_URL/api/v1/fmcsa/verify`
    - Method: `POST`
    - Headers: `{"X-API-Key": "YOUR_API_KEY"}`
    - Body: `{ "mc_number": "{{mc_number}}" }`
    - Create a condition branch based on the `eligible` field in the response.
4.  **Step 3: Search Loads (HTTP Node):**
    - URL: `YOUR_API_URL/api/v1/loads/search`
    - Body: `{ "equipment_type": "...", ... }` (use variables from call)
    - The agent will then read out the details of the first load returned.
5.  **Step 4: Negotiation Loop:**
    - Ask the carrier for their offer.
    - Use an HTTP node to call `/api/v1/negotiations/evaluate`.
    - Use conditions on the `status` response field to either accept, counter-offer, or reject. Loop back if countering, up to 3 times.
6.  **Step 5: Finalize Call (HTTP Node):**
    - URL: `YOUR_API_URL/api/v1/calls/finalize`
    - Body: Populate with all collected variables from the call.
7.  **Step 6: Transfer Call:** If the outcome was "accepted," use the "Transfer Call" node to send the carrier to a human sales rep.

## 4. Deployment to AWS

1.  **RDS:** Create a PostgreSQL instance in RDS. Configure security groups to allow access from the ECS tasks.
2.  **ECR:** Create two repositories in ECR, one for the API (`happyrobot-api`) and one for the frontend (`happyrobot-frontend`).
3.  **Build & Push:**
    - `docker build -t YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/happyrobot-api:latest -f Dockerfile.api .`
    - `docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/happyrobot-api:latest`
    - Repeat for the frontend using `web_client/Dockerfile.prod`.
4.  **ECS (Fargate):**
    - Create a new cluster (e.g., `HappyRobot-FDE`).
    - Create Task Definitions for both API and frontend, pointing to the ECR images and configuring environment variables (including `DATABASE_URL` and `API_KEY` from Secrets Manager).
    - Create two separate services, one for each task definition.
5.  **ALB:**
    - Create an Application Load Balancer.
    - Create two target groups, one for each service.
    - Create listener rules on port 443 (HTTPS): one rule to forward traffic for your API path (`/api/*`) to the API target group, and a default rule to forward all other traffic to the frontend target group.
6.  **ACM:** Request a public SSL certificate in ACM and associate it with the ALB listener to enable HTTPS.
7.  **DNS:** Create a DNS record (e.g., `app.yourdomain.com`) in Route 53 pointing to the ALB.
