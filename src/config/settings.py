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
    app_description: str = (
        "AI-powered workflow automation platform for audit and compliance"
    )
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
    enable_https: bool = Field(default=False, alias="ENABLE_HTTPS")

    # API Base URL
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    # CORS settings
    cors_origins: list = Field(default=["*"], alias="CORS_ORIGINS")

    # Logging settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Business Logic Settings
    max_load_weight_lbs: int = Field(default=80000, alias="MAX_LOAD_WEIGHT_LBS")
    max_reference_number_counter: int = Field(
        default=99999, alias="MAX_REFERENCE_NUMBER_COUNTER"
    )
    max_rate_amount: str = Field(default="999999.99", alias="MAX_RATE_AMOUNT")

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
