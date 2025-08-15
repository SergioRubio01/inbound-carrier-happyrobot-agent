# Contributing to HappyRobot FDE

First off, thank you for considering contributing! Your help is appreciated and welcomed. This document provides guidelines for contributing to the project to make the process as smooth as possible.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Forking & Cloning](#forking--cloning)
  - [Environment Setup](#environment-setup)
- [Development Workflow](#development-workflow)
  - [Running the Application](#running-the-application)
  - [Working with the Database](#working-with-the-database)
  - [Pre-commit Hooks](#pre-commit-hooks)
  - [Coding Style](#coding-style)
  - [Running Tests](#running-tests)
- [Submitting Changes](#submitting-changes)
  - [Branching](#branching)
  - [Committing](#committing)
  - [Pull Requests](#pull-requests)

## Code of Conduct
This project and everyone participating in it is governed by our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Getting Started

### Prerequisites
Make sure you have the following tools installed on your system:
-   [Git](https://git-scm.com/)
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   [Python 3.12+](https://www.python.org/downloads/) & Pip
-   [Node.js 18+](https://nodejs.org/) & NPM

### Forking & Cloning
1.  **Fork** the repository by clicking the "Fork" button on the top right of the repository page on GitHub.
2.  **Clone** your forked repository to your local machine:
    ```bash
    git clone https://github.com/<your-username>/FDE_inbound_carrier_sales.git
    cd FDE_inbound_carrier_sales
    ```

### Environment Setup

1.  **Environment Variables**: Create a local environment file by copying the example. The defaults are configured to work with the local Docker Compose setup.
    ```bash
    cp .env.example .env
    ```

2.  **Frontend Dependencies**: Install the Node.js packages required for the frontend application and the pre-commit hooks.
    ```bash
    cd web_client
    npm install
    cd ..
    ```

## Development Workflow

### Running the Application
The entire development stack is managed via Docker Compose. This is the recommended way to run the application locally.
To build and start all services (API, Frontend, PostgreSQL, pgAdmin), run:
```bash
docker compose up --build
```
The services will be available at:
-   **Backend API**: `http://localhost:8000`
-   **API Docs**: `http://localhost:8000/api/v1/docs`
-   **Frontend App**: `http://localhost:3000`
-   **pgAdmin**: `http://localhost:5050` (Login with `admin@local.host` / `admin`)

The API and frontend services are configured with hot-reloading. When you save a file, the relevant service will automatically restart to apply the changes.

### Working with the Database
You can connect to the PostgreSQL database using pgAdmin (available at `http://localhost:5050`) or any other database client with the following details from your `.env` file:
-   **Host**: `localhost`
-   **Port**: `5432`
-   **User**: `happyrobot`
-   **Password**: `happyrobot`
-   **Database Name**: `happyrobot`

#### Database Migrations
This project uses Alembic for database migrations.

-   To apply all migrations to your database:
    ```bash
    docker exec happyrobot-api alembic upgrade head
    ```
-   To create a new migration after changing SQLAlchemy models:
    ```bash
    docker exec happyrobot-api alembic revision --autogenerate -m "Your descriptive migration message"
    ```

### Pre-commit Hooks
We use pre-commit hooks to enforce code style and quality automatically before you commit.
1.  **Install pre-commit**:
    ```bash
    pip install pre-commit
    ```
2.  **Install hooks**:
    ```bash
    pre-commit install
    ```
Now, hooks will run on your staged files before each commit. If a hook fails, it may auto-fix the files. If so, just `git add` the changes and commit again.

### Coding Style
-   **Backend**: Follows `Black` for formatting, `isort` for imports, and `ruff` for linting. The architecture is hexagonal; please respect the separation of concerns between `core`, `infrastructure`, and `interfaces`.
-   **Frontend**: Follows `Prettier` for formatting and `ESLint` for linting.

### Running Tests
-   **Backend Tests**: To run all backend tests, execute the following command:
    ```bash
    docker exec happyrobot-api pytest
    ```
-   **Frontend Tests**: To run frontend tests:
    ```bash
    cd web_client
    npm test
    ```

## Submitting Changes

### Branching
Create a new branch for your feature or bug fix. Use a descriptive prefix like `feature/` or `fix/`.
```bash
git checkout -b feature/add-negotiation-logic
```

### Committing
Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in maintaining a clear and automated changelog.
-   `feat`: A new feature
-   `fix`: A bug fix
-   `docs`: Documentation only changes
-   `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
-   `refactor`: A code change that neither fixes a bug nor adds a feature
-   `test`: Adding missing tests or correcting existing tests

### Pull Requests
-   Push your branch to your fork and open a pull request against the `main` branch of the original repository.
-   Provide a clear title and a detailed description of the changes.
-   If your PR addresses an existing issue, link it in the description (e.g., `Closes #123`).
-   Ensure all automated checks and tests are passing before requesting a review.
