#!/bin/sh
set -e

echo "=== HappyRobot API Startup ==="
echo "Current working directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# Skip DATABASE_URL construction if explicitly set
if [ ! -z "$DATABASE_URL" ]; then
  echo "Using explicit DATABASE_URL configuration"

elif [ ! -z "$POSTGRES_HOST" ] && [ ! -z "$POSTGRES_USER" ] && [ ! -z "$POSTGRES_PASSWORD" ] && [ ! -z "$POSTGRES_DB" ]; then
  # Local PostgreSQL Configuration (Local development)
  POSTGRES_PORT=${POSTGRES_PORT:-5432}

  # Build DATABASE_URL for local development
  export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
  export DATABASE_URL_SYNC="${DATABASE_URL}"
  echo "Built DATABASE_URL for local development"

  # Handle AWS Secrets Manager JSON format for POSTGRES_PASSWORD (fallback for mixed deployments)
  if echo "$POSTGRES_PASSWORD" | grep -q '^{.*"password".*}$'; then
    echo "Extracting PostgreSQL credentials from AWS Secrets Manager JSON"
    EXTRACTED_PASSWORD=$(echo "$POSTGRES_PASSWORD" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('password', ''))" 2>/dev/null || echo "")
    EXTRACTED_USER=$(echo "$POSTGRES_PASSWORD" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('username', ''))" 2>/dev/null || echo "")

  fi

else
  echo "Warning: No valid database configuration found. Falling back to application defaults."
fi

# Debug environment variables
echo "=== Database Configuration ==="
echo "DATABASE_URL: ${DATABASE_URL:-NOT_SET}"
echo "DATABASE_URL_SYNC: ${DATABASE_URL_SYNC:-NOT_SET}"
echo "POSTGRES_DB: ${POSTGRES_DB:-NOT_SET}"
echo "POSTGRES_USER: ${POSTGRES_USER:-NOT_SET}"

echo "=== Waiting for database to be ready ==="
# Determine database host and port
if [ ! -z "$DATABASE_URL" ]; then
  # Extract host and port from DATABASE_URL
  # Format: postgresql://username:password@host:port/database
  DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
  DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
elif [ ! -z "$POSTGRES_HOST" ]; then
  # Use POSTGRES_HOST/PORT directly
  DB_HOST="$POSTGRES_HOST"
  DB_PORT="${POSTGRES_PORT:-5432}"
elif [ ! -z "$DATABASE_HOST" ]; then
  # Use DATABASE_HOST/PORT directly (ECS)
  DB_HOST="$DATABASE_HOST"
  DB_PORT="${DATABASE_PORT:-5432}"
else
  echo "WARNING: No database configuration found, using defaults"
  DB_HOST="postgres"
  DB_PORT="5432"
fi

# Wait for database to be ready
while ! nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  sleep 2
done

echo "PostgreSQL is ready at $DB_HOST:$DB_PORT!"

# Give it a bit more time to ensure the database is fully initialized
sleep 2

# Ensure we're in the correct working directory
cd /app

echo "=== Checking alembic configuration ==="
if [ ! -f "alembic.ini" ]; then
  echo "ERROR: alembic.ini not found in $(pwd)"
  ls -la
  exit 1
fi

if [ ! -d "migrations" ]; then
  echo "ERROR: migrations directory not found in $(pwd)"
  ls -la
  exit 1
fi

echo "=== Checking database state ==="
# Check if this is an empty database that needs initialization
python -c "
import sys
import os
from sqlalchemy import create_engine, text

# Get the DATABASE_URL_SYNC from environment (set by this script)
database_url = os.environ.get('DATABASE_URL_SYNC')
if not database_url:
    # Fallback to importing settings if no DATABASE_URL_SYNC
    from src.config.settings import settings
    database_url = settings.get_sync_database_url

engine = create_engine(database_url)
with engine.connect() as conn:
    # Check if alembic_version table exists
    result = conn.execute(text(
        \"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')\"
    ))
    alembic_exists = result.scalar()

    if not alembic_exists:
        print('EMPTY_DATABASE')
        sys.exit(0)
    else:
        print('MIGRATIONS_ONLY')
        sys.exit(0)
"
DB_STATE=$?

if [ "$DB_STATE" = "0" ]; then
  DB_STATUS=$(python -c "
import sys
import os
from sqlalchemy import create_engine, text

# Get the DATABASE_URL_SYNC from environment (set by this script)
database_url = os.environ.get('DATABASE_URL_SYNC')
if not database_url:
    # Fallback to importing settings if no DATABASE_URL_SYNC
    from src.config.settings import settings
    database_url = settings.get_sync_database_url

engine = create_engine(database_url)
with engine.connect() as conn:
    result = conn.execute(text(
        \"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')\"
    ))
    alembic_exists = result.scalar()

    if not alembic_exists:
        print('EMPTY_DATABASE')
    else:
        print('MIGRATIONS_ONLY')
")

  echo "Database state: $DB_STATUS"

  if [ "$DB_STATUS" = "EMPTY_DATABASE" ]; then
    echo "=== Initializing empty database ==="
    if python scripts/init_empty_database.py --force; then
      echo "Database initialized successfully!"
    else
      echo "ERROR: Failed to initialize database"
      exit 1
    fi
  elif [ "$DB_STATUS" = "MIGRATIONS_ONLY" ]; then
    echo "=== Running database migrations ==="
    # Retry migrations a few times in case of connection issues
    MAX_RETRIES=5
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
      echo "Migration attempt $((RETRY_COUNT + 1))/$MAX_RETRIES"
      if alembic upgrade head; then
        echo "Database migrations completed successfully!"
        break
      else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Migration failed. Retrying... ($RETRY_COUNT/$MAX_RETRIES)"
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
          sleep 3
        fi
      fi
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
      echo "ERROR: Failed to run migrations after $MAX_RETRIES attempts"
      exit 1
    fi
  else
    echo "=== Running database migrations ==="
    alembic upgrade head || echo "Migrations may have already been applied"
  fi
else
  echo "ERROR: Failed to check database state"
  exit 1
fi

# Telegram bot removed - now using webhook-based Lambda bot instead

echo "=== Starting HappyRobot API server ==="

# Check if we're in development mode
if [ "$ENVIRONMENT" = "dev" ] || [ "$ENVIRONMENT" = "local" ]; then
  echo "Starting in development mode with reload enabled"
  exec uvicorn src.interfaces.api.app:create_app \
      --host 0.0.0.0 \
      --port 8000 \
      --reload \
      --factory \
      --log-level info
else
  echo "Starting in production mode"
  exec uvicorn src.interfaces.api.app:create_app \
      --host 0.0.0.0 \
      --port 8000 \
      --factory \
      --log-level info \
      --workers 1
fi
