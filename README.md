# FDE Technical Challenge: Inbound Carrier Sales (HappyRobot)

## Overview
This repository contains a working proof-of-concept for automating inbound carrier load sales using the HappyRobot platform. The solution implements an inbound agent that answers carrier calls, authenticates them (MC), searches viable loads, negotiates price, classifies the call outcome and sentiment, and hands off the call to a sales rep when an agreement is reached.

The backend follows a hexagonal architecture in `src/`:
- `src/config`: environment configuration
- `src/core`: domain, ports, and application logic
- `src/infrastructure`: adapters (database, external APIs)
- `src/interfaces`: API endpoints and middleware

Frontend lives in `web_client/` (Next.js). For this POC we only use REST—no WebSockets are required.

## Tech stack (as required)
- **AWS RDS for PostgreSQL** (with pgAdmin locally)
- **ECS (Fargate)** for backend and frontend as two images
- **Docker Compose** for local development
- **FastAPI** for REST API (Python 3.12)
- **Next.js 15** for the dashboard/report UI
- Security: **HTTPS (in AWS with ALB/ACM)** and **API Key** authentication for all API endpoints
- Note: No WebSocket, no Redis, no backups services in this architecture

## Architecture summary
- A single FastAPI service exposes REST endpoints for:
  - MC verification (proxy to FMCSA)
  - Load search and selection
  - Negotiation handling (state limited to 3 back-and-forths)
  - Call extraction, outcome classification, and sentiment tagging
  - Metrics aggregation for the dashboard
- A PostgreSQL database stores loads and call transcripts/metadata.
- The HappyRobot agent invokes these endpoints via web call triggers.
- The Next.js dashboard queries the API and renders KPIs and reports.

## Repository layout
- `src/`: hexagonal API (config, core, infrastructure, interfaces)
- `web_client/`: Next.js app for the dashboard
- `Dockerfile.api`: API container image
- `docker-compose.yml`: local dev with Postgres, pgAdmin, API, and frontend
- `docs/IMPLEMENTATION_PLAN.md`: detailed implementation plan

## Local development

### Prerequisites
- Docker Desktop
- Node 18+ (optional if using Docker only)

### Environment
Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Minimum required env vars:
- `POSTGRES_DB=happyrobot`
- `POSTGRES_USER=happyrobot`
- `POSTGRES_PASSWORD=happyrobot`
- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `API_KEY=dev-local-api-key`

### Start services
```bash
docker compose up --build
```

Services:
- API: http://localhost:8000 (health at `/api/v1/health`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432
- pgAdmin: http://localhost:5050 (default: admin@local / admin)

To access Postgres in pgAdmin, register a new server:
- Host: `postgres`
- Port: `5432`
- Username: `POSTGRES_USER`
- Password: `POSTGRES_PASSWORD`

### Security (API key)
All endpoints require an API key via either header:
- `X-API-Key: <your-key>`
- or `Authorization: ApiKey <your-key>`

Exempt: `/health`, `/api/v1/health`, `/api/v1/openapi.json`, `/api/v1/docs`, `/api/v1/redoc`.

## Database

### Loads schema
Minimum fields per load:
- `load_id` (UUID/PK)
- `origin`
- `destination`
- `pickup_datetime`
- `delivery_datetime`
- `equipment_type`
- `loadboard_rate`
- `notes`
- `weight`
- `commodity_type`
- `num_of_pieces`
- `miles`
- `dimensions`

You can create the table and seed example loads via pgAdmin or migrations. See `docs/IMPLEMENTATION_PLAN.md` for a ready-to-use SQL block.

## HappyRobot platform: manual steps to connect the agentic workflow
The solution uses the web call trigger and REST callbacks (no purchased phone numbers).

1) Create an agent “Inbound Carrier Sales”
- Capability: Voice
- Trigger: Web Call Trigger
- Greeting prompt (example):
  "Thank you for calling Acme Logistics. I can help match your truck to available loads. May I have your MC number to get started?"

2) MC verification step
- Action: HTTP POST to `POST /api/v1/fmcsa/verify`
- Payload:
  `{ "mc_number": "{{call.caller_provided_mc}}" }`
- Success condition: `eligible == true` → continue; else reply with eligibility failure and end.

3) Load matching step
- Action: HTTP POST to `POST /api/v1/loads/search`
- Payload includes carrier lane, equipment, dates gathered during the call
- Response returns a set of viable loads with details to pitch
- Agent pitches the top 1–3 loads:
  "I have a load from {{origin}} to {{destination}} picking up {{pickup_datetime}} with {{equipment_type}} at ${{loadboard_rate}}. Would you like to proceed or make an offer?"

4) Negotiation loop (up to 3 back-and-forths)
- Action: HTTP POST to `POST /api/v1/negotiations/evaluate`
- Payload includes `load_id`, `carrier_offer`, and `context`
- Response returns `counter_offer` or `accepted: true`
- If accepted → proceed to hand-off step

5) Hand-off to sales rep
- Action: HTTP POST to `POST /api/v1/calls/handoff`
- Payload includes `load_id`, `agreed_rate`, `carrier_contact`, and call summary
- The API returns handoff metadata and dials/bridges using your internal process; for POC we just log and return a "ready to transfer" response.

6) Extraction + classification
- Action: HTTP POST to `POST /api/v1/calls/finalize`
- Provide call transcript or structured values collected by the agent
- API returns:
  - `extracted_fields` (MC, DAT points, notes)
  - `outcome_class` (accepted/declined/callback/no-eligible)
  - `sentiment` (positive/neutral/negative)

7) Metrics dashboard
- The frontend queries `GET /api/v1/metrics/summary` and renders KPIs such as:
  - Total calls, eligible carriers, matched loads, accepted offers, average negotiation steps, average agreed rate vs. loadboard rate, sentiment distribution

Note: The exact JSON schemas are documented in `docs/IMPLEMENTATION_PLAN.md` with request/response examples you can paste into HappyRobot’s HTTP steps.

## Deployment (AWS ECS / RDS)
High level steps:
1) Provision RDS PostgreSQL and import the schema
2) Build and push two images to ECR:
   - API image from `Dockerfile.api`
   - Frontend image from `web_client/Dockerfile.prod`
3) Create two ECS Fargate services (API, Frontend) behind an ALB (two target groups) with a single task each under the same cluster HappyRobot-FDE
4) Attach HTTPS certificate via ACM to ALB
5) Configure environment variables and secrets (RDS URL, `API_KEY`, etc.) in ECS Task Definitions
6) Point frontend env `NEXT_PUBLIC_API_URL` to the API’s public ALB domain

## Deliverables (templates)

### 1) Email to prospect (Carlos Becker)
Subject: HappyRobot Inbound Carrier Sales – POC Progress and Demo Readiness

Hi Carlos,

Ahead of our meeting, here’s a quick update on the POC:
- Implemented an inbound voice agent that authenticates carriers by MC via FMCSA, finds viable loads, and negotiates up to three rounds.
- Built a REST API with API key security that the agent calls using web call triggers (no phone purchase needed).
- Added an analytics dashboard showing core KPIs for adoption and performance.
- Containerized both API and frontend; deployment plan prepared for ECS Fargate with RDS.

For the demo, I’ll walk through the agent workflow, a short negotiation scenario, and the dashboard. Please let me know if you’d like any additional metrics or flows highlighted.

Best regards,

[Your Name]
CC: [Recruiter Name]

### 2) Build description for broker (Acme Logistics)
A 1–2 page description covering objectives, flow, data handled, and security is included in `docs/IMPLEMENTATION_PLAN.md` (Executive Summary section). You can share it directly with stakeholders.

### 3) Link to repository
Provide: [Fill with your repo URL]

### 4) Link to configured campaign in HappyRobot
Provide: [Fill with your HappyRobot campaign URL]

### 5) Short video (5 minutes)
Cover:
- Use case setup (agent flow)
- Short demo (MC → match → negotiate → handoff)
- Dashboard tour (KPIs)

## Notes
- This POC intentionally avoids WebSockets and Redis. All interactions are REST-based and state is persisted in Postgres.
- Backups are managed at the RDS level in production; no extra backup service is run locally.


## Contributing
We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment, run tests, and submit a pull request.

All contributors are expected to adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
