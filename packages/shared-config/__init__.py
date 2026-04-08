"""Shared configuration for the real-time content ranking system."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Service Configuration
    SERVICE_NAME: str = "ranking-service"
    SERVICE_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "rankinguser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "rankingpass")
    DB_NAME: str = os.getenv("DB_NAME", "ranking_db")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # Resilience Configuration
    HTTP_CLIENT_RETRY_MAX_ATTEMPTS: int = int(
        os.getenv("HTTP_CLIENT_RETRY_MAX_ATTEMPTS", "3")
    )
    HTTP_CLIENT_RETRY_INITIAL_DELAY_SECONDS: float = float(
        os.getenv("HTTP_CLIENT_RETRY_INITIAL_DELAY_SECONDS", "0.1")
    )
    HTTP_CLIENT_RETRY_MAX_DELAY_SECONDS: float = float(
        os.getenv("HTTP_CLIENT_RETRY_MAX_DELAY_SECONDS", "1.0")
    )
    HTTP_CLIENT_RETRY_BACKOFF_MULTIPLIER: float = float(
        os.getenv("HTTP_CLIENT_RETRY_BACKOFF_MULTIPLIER", "2.0")
    )
    KAFKA_PUBLISH_RETRY_MAX_ATTEMPTS: int = int(
        os.getenv("KAFKA_PUBLISH_RETRY_MAX_ATTEMPTS", "3")
    )
    KAFKA_PUBLISH_RETRY_INITIAL_DELAY_SECONDS: float = float(
        os.getenv("KAFKA_PUBLISH_RETRY_INITIAL_DELAY_SECONDS", "0.1")
    )
    KAFKA_PUBLISH_RETRY_MAX_DELAY_SECONDS: float = float(
        os.getenv("KAFKA_PUBLISH_RETRY_MAX_DELAY_SECONDS", "1.0")
    )
    KAFKA_PUBLISH_RETRY_BACKOFF_MULTIPLIER: float = float(
        os.getenv("KAFKA_PUBLISH_RETRY_BACKOFF_MULTIPLIER", "2.0")
    )

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

__all__ = ["Settings", "settings"]
