"""
File: settings.py
Description: Unified configuration settings for HappyRobot
Author: HappyRobot Team
Created: 2025-05-30
"""

from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    app_name: str = "HappyRobot FDE"
    app_description: str = "AI-powered workflow automation platform for audit and compliance"
    app_version: str = "1.0.0"

    # Environment settings
    environment: str = Field(
        default="local",
        alias="ENVIRONMENT",
        description="Current environment (local, dev, staging, prod)",
    )

    # Database settings
    postgres_db: str = Field(default="happyrobot", alias="POSTGRES_DB")
    postgres_user: str = Field(default="happyrobot", alias="POSTGRES_USER")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_password: str = Field(default="happyrobot", alias="POSTGRES_PASSWORD")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_recycle: int = Field(default=3600, alias="DATABASE_POOL_RECYCLE")
    database_echo_sql: bool = Field(default=False, alias="DATABASE_ECHO_SQL")

    # Security settings
    api_key: str = Field(default="dev-local-api-key", alias="API_KEY")

    # API Base URL
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    # CORS settings
    cors_origins: list = Field(default=["*"], alias="CORS_ORIGINS")

    # Logging settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # FMCSA API Configuration
    fmcsa_api_key: str = Field(alias="FMCSA_API_KEY")
    fmcsa_api_base_url: str = Field(
        default="https://mobile.fmcsa.dot.gov/qc/services",
        alias="FMCSA_API_BASE_URL"
    )
    fmcsa_api_timeout: int = Field(default=30, alias="FMCSA_API_TIMEOUT")
    fmcsa_cache_ttl: int = Field(default=86400, alias="FMCSA_CACHE_TTL")  # 24 hours
    fmcsa_enable_cache: bool = Field(default=True, alias="FMCSA_ENABLE_CACHE")
    fmcsa_max_retries: int = Field(default=3, alias="FMCSA_MAX_RETRIES")
    fmcsa_backoff_factor: float = Field(default=2.0, alias="FMCSA_BACKOFF_FACTOR")

    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )

    @property
    def get_sync_database_url(self) -> str:
        """Get the synchronous database URL for Alembic migrations."""
        encoded_password = quote_plus(self.postgres_password)
        encoded_user = quote_plus(self.postgres_user)
        return f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def get_async_database_url(self) -> str:
        """Get the asynchronous database URL for the application."""
        encoded_password = quote_plus(self.postgres_password)
        encoded_user = quote_plus(self.postgres_user)
        return f"postgresql+asyncpg://{encoded_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


# Create settings instance
settings = Settings()
