# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HappyRobot FDE - Inbound Carrier Sales automation platform using voice AI agents for logistics operations. The system authenticates carriers, matches loads, negotiates rates, and hands off to sales reps.

## Architecture

**Hexagonal Architecture** in backend (`src/`):
- `src/config`: Environment configuration and settings
- `src/core`: Business logic organized as:
  - `domain`: Entities, value objects, exceptions
  - `application`: Use cases and services
  - `ports`: Interfaces for external dependencies
- `src/infrastructure`: External service implementations (DB, APIs)
  - `database/models`: Database models
  - `database/postgres`: Postgres implementation of models
- `src/interfaces/api/v1`: FastAPI endpoints and middleware

**Frontend**: Next.js 15 app in `web_client/` with TypeScript, React Query, and shadcn/ui components

**Infrastructure**: AWS ECS Fargate deployment with RDS PostgreSQL, managed via Pulumi IaC in `infrastructure/pulumi/`

**Migrations**: Database migrations are in `migrations/versions`. Every time there is a change in database models, a new migration shall be created.

## Essential Commands

### Local Development
```bash
# Start all services (API, Frontend, PostgreSQL, pgAdmin)
docker compose up --build

# Run only backend API locally
python main.py

# Frontend development
cd web_client
npm run dev
```

### Testing
```bash
# Backend tests (using pytest)
pytest
pytest -v -s  # Verbose with stdout
pytest tests/unit/  # Run specific test directory
pytest -k "test_name"  # Run specific test by name

# Frontend tests
cd web_client
npm run test  # Jest unit tests
npm run test:e2e  # Playwright E2E tests
npm run test:all  # Run all tests
```

### Code Quality
```bash
# Backend
ruff check .  # Linting
ruff format .  # Formatting
mypy .  # Type checking

# Frontend
cd web_client
npm run lint  # ESLint
npm run lint:fix  # Fix linting issues
npm run format  # Prettier formatting
npm run type-check  # TypeScript check
```

### Database Operations
```bash
# Run migrations (Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1

# Access database
docker exec -it happyrobot-postgres psql -U happyrobot -d happyrobot
```

### Deployment (Pulumi)
```bash
cd infrastructure/pulumi
npm install
pulumi stack select happyrobot-dev
pulumi login
pulumi up  # Deploy infrastructure
pulumi destroy  # Tear down
```

## API Authentication

All API endpoints require API key authentication via headers:
- `X-API-Key: <key>` or `Authorization: ApiKey <key>`

Exempt endpoints: `/health`, `/api/v1/health`, `/api/v1/docs`, `/api/v1/openapi.json`

## Key API Endpoints

- `POST /api/v1/fmcsa/verify` - Verify carrier MC number eligibility
- `POST /api/v1/loads/search` - Search available loads
- `POST /api/v1/negotiations/evaluate` - Handle price negotiation
- `POST /api/v1/calls/handoff` - Transfer to sales rep
- `POST /api/v1/calls/finalize` - Extract call data and classify outcome
- `GET /api/v1/metrics/summary` - Dashboard KPIs

## Database Schema

Main tables:
- `loads`: Available freight loads with origin, destination, rates, equipment
- `calls`: Call transcripts and metadata
- `negotiations`: Negotiation history and outcomes
- `carriers`: Verified carrier information

## Environment Variables

Required in `.env`:
```
POSTGRES_DB=happyrobot
POSTGRES_USER=happyrobot
POSTGRES_PASSWORD=happyrobot
POSTGRES_HOST=postgres
API_KEY=dev-local-api-key
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=eu-south-2
```

## Service URLs

Local development:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- pgAdmin: http://localhost:5050 (admin@local/admin)

## HappyRobot Platform Integration

The system integrates with HappyRobot voice agents via REST webhooks:
1. Agent authenticates carrier via MC number
2. Searches and presents matching loads
3. Handles up to 3 rounds of price negotiation
4. Transfers accepted deals to sales reps
5. Extracts and classifies call outcomes

Each step uses HTTP POST to the API endpoints with appropriate JSON payloads.

## Testing Guidelines

- Backend: Tests in `src/tests/` following pytest conventions
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.aws`
- Frontend: Jest for unit tests, Playwright for E2E in `web_client/src/tests/`
- Mock external services (AWS, FMCSA) in tests

## Development Workflow

1. Create feature branch from `master`
2. Implement changes following hexagonal architecture patterns
3. Write/update tests for new functionality
4. Run linting and type checking
5. Test locally with Docker Compose
6. Create pull request with clear description

## Performance Considerations

- PostgreSQL optimized with connection pooling (max 200 connections)
- API uses async/await for I/O operations
- Frontend implements React Query for efficient data fetching
- Database indexes on frequently queried fields (MC number, load status)
