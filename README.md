# Inbound Carrier Sales (HappyRobot) API

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack-as-required)
- [Repository Layout](#repository-layout)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Metrics and Reporting](#metrics-and-reporting)
- [Contributing](#contributing)

## Overview
This repository contains a working proof-of-concept for automating inbound carrier load sales using the HappyRobot platform. The solution implements an inbound agent that answers carrier calls, authenticates them (MC), searches viable loads, negotiates price, classifies the call outcome and sentiment, and hands off the call to a sales rep when an agreement is reached.

The API serves as the backend for HappyRobot platform integration. For this POC we only use REST—no WebSockets are required.

## Tech stack (as required)
- **AWS RDS for PostgreSQL** (with pgAdmin locally)
- **ECS (Fargate)** for backend deployment
- **Docker Compose** for local development
- **FastAPI** for REST API (Python 3.12)
- Security: **HTTPS (in AWS with ALB/ACM)** and **API Key** authentication for all API endpoints
- Note: No WebSocket, no Redis, no backup services in this architecture

## Repository layout
- `src/`: API source code
- `docker-compose.yml`: local dev with Postgres, pgAdmin, and API
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

### Generate self-signed certificates (optional for HTTPS locally)
```bash
# Generate self-signed cert for local HTTPS testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

### Start services
```bash
docker compose up --build
```

Services:
- API: http://localhost:8000 (health at `/api/v1/health`)
- Postgres: localhost:5432
- pgAdmin: http://localhost:5050/browser (default: admin@local.host / admin)

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

## Deployment
For detailed deployment instructions to AWS ECS/RDS, please refer to the [Deployment Guide](docs/DEPLOYMENT.md).

## Metrics and Reporting
For detailed instructions on using the metrics CLI tool to generate call analytics reports, see [METRICS.md](METRICS.md). The CLI allows you to:
- Generate PDF reports with call statistics and sentiment analysis
- Export metrics data as JSON for further analysis
- Schedule automated reports for monitoring performance

Quick start:
```bash
poetry run python -m src.interfaces.cli --api-key YOUR_KEY
```

## Contributing
We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment, run tests, and submit a pull request.

All contributors are expected to adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
