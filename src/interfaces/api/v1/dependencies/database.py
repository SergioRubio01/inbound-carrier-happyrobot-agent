"""
Database dependency for API endpoints.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import get_database_session as _get_database_session


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a real database session for API endpoints.

    This function provides a database session that is properly managed
    with connection pooling and automatic cleanup.
    """
    async for session in _get_database_session():
        yield session
