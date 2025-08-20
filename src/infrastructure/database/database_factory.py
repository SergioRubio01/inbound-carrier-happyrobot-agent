"""
File: database_factory.py
Description: Database factory for creating PostgreSQL connections
Author: HappyRobot Team
Created: 2025-07-04
"""

import logging

from src.config.settings import Settings
from src.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory for creating database connections based on configuration"""

    @staticmethod
    def create_connection(settings: Settings) -> DatabaseConnection:
        """
        Create a standard PostgreSQL connection.

        Args:
            settings: Application settings

        Returns:
            A DatabaseConnection instance.
        """
        logger.info("Creating standard PostgreSQL connection")
        return DatabaseConnection(
            database_url=settings.get_async_database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            settings=settings,
        )

    @staticmethod
    def get_database_url(settings: Settings, sync: bool = False) -> str:
        """
        Get database URL based on configuration.

        Args:
            settings: Application settings
            sync: Whether to return synchronous URL for Alembic

        Returns:
            Database connection URL string
        """
        if sync:
            return settings.get_sync_database_url
        return settings.get_async_database_url
