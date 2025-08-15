#!/usr/bin/env python3
"""
Initialize an empty database with proper table creation and alembic setup.

This script is designed to handle the case where an RDS database is empty
but needs to be initialized with all the AutoAudit tables and proper
alembic migration tracking.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

from src.config.settings import settings
from src.infrastructure.database.base import Base
from src.infrastructure.database.models import *  # noqa: F401,F403

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with all tables and set proper alembic version."""

    # Get sync database URL
    database_url = settings.get_sync_database_url
    logger.info(f"Connecting to database...")

    # Create engine
    engine = create_engine(database_url)

    try:
        # First, check if alembic_version table exists and clear it
        with engine.begin() as conn:
            # Check if alembic_version exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'alembic_version')"
            ))
            alembic_exists = result.scalar()

            if alembic_exists:
                logger.info("Clearing existing alembic_version...")
                conn.execute(text("DELETE FROM alembic_version"))

            # Check if any tables exist
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            ))
            table_count = result.scalar()
            logger.info(f"Found {table_count} existing tables")

        # Create all tables using SQLAlchemy
        logger.info("Creating all database tables...")
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully")

        # Now stamp alembic to the latest version
        alembic_cfg = Config("alembic.ini")

        # Stamp to the latest revision
        logger.info("Stamping database with latest alembic revision...")
        command.stamp(alembic_cfg, "head")
        logger.info("Database stamped successfully")

        # Verify the setup
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            logger.info(f"Current alembic version: {version}")

            # Count tables again
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            ))
            final_table_count = result.scalar()
            logger.info(f"Total tables after initialization: {final_table_count}")

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        engine.dispose()


def main():
    """Main entry point."""
    logger.info("AutoAudit Database Initialization Script")
    logger.info("=" * 50)

    # Show configuration
    logger.info("Database Configuration:")
    logger.info(f"  Host: {settings.postgres_host}")
    logger.info(f"  Port: {settings.postgres_port}")
    logger.info(f"  Database: {settings.postgres_db}")
    logger.info(f"  User: {settings.postgres_user}")

    # Confirm before proceeding
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        logger.info("Running in force mode, skipping confirmation...")
    else:
        response = input("\nThis will initialize the database. Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

    # Initialize the database
    init_database()


if __name__ == "__main__":
    main()
