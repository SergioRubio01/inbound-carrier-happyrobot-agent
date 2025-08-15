# FDE Technical Challenge: Inbound Carrier Sales (HappyRobot)

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack-as-required)
- [Architecture Summary](#architecture-summary)
- [Repository Layout](#repository-layout)
- [Local Development](#local-development)
- [HappyRobot Platform: Manual Steps](#happyrobot-platform-manual-steps-to-connect-the-agentic-workflow)
- [Deployment (AWS ECS / RDS)](#deployment-aws-ecs--rds)
- [Contributing](#contributing)

## Overview
This repository contains a working proof-of-concept for automating inbound carrier load sales using the HappyRobot platform. The solution implements an inbound agent that answers carrier calls, authenticates them (MC), searches viable loads, negotiates price, classifies the call outcome and sentiment, and hands off the call to a sales rep when an agreement is reached.

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

For a detailed architecture overview, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout
- `src/`: API source code
- `web_client/`: Next.js app for the dashboard
- `docker-compose.yml`: local dev with Postgres, pgAdmin, API, and frontend
- `docs/DEPLOYMENT.md`: detailed deployment guide

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

## HappyRobot platform: manual steps to connect the agentic-workflow
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
This section provides a high-level overview. For detailed, step-by-step instructions, please refer to the [Deployment Guide](docs/DEPLOYMENT.md).

High level steps:
1) Provision RDS PostgreSQL and import the schema
2) Build and push two images to ECR:
   - API image from `Dockerfile.api`
   - Frontend image from `web_client/Dockerfile.prod`
3) Create two ECS Fargate services (API, Frontend) behind an ALB (two target groups) with a single task each under the same cluster HappyRobot-FDE
4) Attach HTTPS certificate via ACM to ALB
5) Configure environment variables and secrets (RDS URL, `API_KEY`, etc.) in ECS Task Definitions
6) Point frontend env `NEXT_PUBLIC_API_URL` to the API’s public ALB domain

## Contributing
We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment, run tests, and submit a pull request.

All contributors are expected to adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
