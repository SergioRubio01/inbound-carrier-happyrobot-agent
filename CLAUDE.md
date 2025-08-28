# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HappyRobot FDE - Inbound Carrier Sales automation platform using voice AI agents for logistics operations. The system matches loads, negotiates rates, and hands off to sales reps. Carrier authentication and verification is handled by the HappyRobot workflow platform.

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

**Infrastructure**: AWS ECS Fargate deployment with RDS PostgreSQL, managed via Pulumi IaC in `infrastructure/pulumi/`

**Migrations**: Database migrations are in `migrations/versions`. Every time there is a change in database models, a new migration shall be created.

## Essential Commands

### Local Development
```bash
# Start all services (API, PostgreSQL, pgAdmin)
docker compose up --build

# Run only backend API locally
python main.py
```

### Testing
```bash
# Backend tests (using pytest)
pytest
pytest -v -s  # Verbose with stdout
pytest tests/unit/  # Run specific test directory
pytest -k "test_name"  # Run specific test by name

```

### Code Quality
```bash
# Backend
ruff check .  # Linting
ruff format .  # Formatting
mypy .  # Type checking

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

- `POST /api/v1/loads/search` - Search available loads
- `GET /api/v1/metrics/summary` - Dashboard KPIs

## Database Schema

Main tables:
- `loads`: Available freight loads with origin, destination, rates, equipment
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
- PostgreSQL: localhost:5432
- pgAdmin: http://localhost:5050 (admin@local/admin)

## HappyRobot Platform Integration

The system integrates with HappyRobot voice agents via REST webhooks:
1. Agent authenticates and verifies carriers (handled by HappyRobot workflow platform)
2. Searches and presents matching loads
3. Transfers accepted deals to sales reps
4. Extracts and classifies call outcomes

Each step uses HTTP POST to the API endpoints with appropriate JSON payloads.

## Testing Guidelines

- Backend: Tests in `src/tests/` following pytest conventions
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.aws`
- Mock external services (AWS) in tests

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
- Database indexes on frequently queried fields (MC number, load status)

- We are not creating a frontend in this project. Only backend is needed
- When user shows a screenshot with HappyRobot platform advancements, tell him in screen additional enhancements the user will manually apply, including settings of each new block
- Use subagents when tasks are long, to preserve more context space
- Never run a aws cli command to deploy changes. Use pulumi unless it is a permissions issue
- use .is() method in sqlalchemy for boolean comparisons in queries
- If and only if the user tells you, commit your changes with pre-commit hooks checks passed successfully. Otherwise, the user will manually do it
- After the user has created a PR, go check the errors if the user tells you there are errors.
- Use cerebras-mcp mcp to create/make edits in files.
