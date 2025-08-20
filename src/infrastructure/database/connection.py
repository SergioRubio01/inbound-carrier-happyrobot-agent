import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager for PostgreSQL"""

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the database connection.

        Args:
            database_url: Database connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            settings: Application settings
        """
        self.settings = settings
        self.database_url = database_url or (
            self.settings.get_async_database_url if self.settings else None
        )
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine = None
        self.session_factory = None

        if not self.database_url:
            raise ValueError("Database URL is required for database connection")

    def initialize(self):
        """Initialize database connection and session factory"""
        logger.info("Initializing standard database connection...")

        pool_size = (
            self.settings.database_pool_size if self.settings else self.pool_size
        )
        max_overflow = (
            self.settings.database_max_overflow if self.settings else self.max_overflow
        )
        pool_recycle = self.settings.database_pool_recycle if self.settings else 3600
        pool_pre_ping = True

        # Create engine with connection pooling
        self.engine = create_async_engine(
            self.database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            echo=self.settings.database_echo_sql if self.settings else False,
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "application_name": (
                        self.settings.app_name if self.settings else "HappyRobot"
                    ),
                    "timezone": "UTC",
                },
            },
        )

        # Create session factory using async_sessionmaker
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

        logger.info("Database connection initialized successfully")

    async def get_engine(self):
        """Get the database engine"""
        return self.engine

    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self.session_factory:
            raise RuntimeError("Database connection not initialized")

        return self.session_factory()

    async def create_tables(self):
        """Create all tables defined in models"""
        from .base import Base

        engine = await self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def health_check(self) -> bool:
        """Check if the database connection is healthy"""
        try:
            engine = await self.get_engine()
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def initialize_database_connection(settings: Settings) -> DatabaseConnection:
    """Initialize the global database connection"""
    global _db_connection

    if _db_connection is None:
        _db_connection = DatabaseConnection(settings=settings)
        _db_connection.initialize()

    return _db_connection


async def get_database_session() -> AsyncSession:
    """Dependency function for FastAPI to get database session"""
    if _db_connection is None:
        from src.config.settings import settings

        initialize_database_connection(settings)

    session = await _db_connection.get_session()
    try:
        yield session
    finally:
        await session.close()
