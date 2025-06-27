"""Development settings for local environment."""

from .settings import Settings


class DevSettings(Settings):
    """Development-specific settings."""

    # Use SQLite for development
    database_url: str = "sqlite:///./jmeter_toolkit.db"
    database_echo: bool = True

    # Disable Celery for development (use synchronous execution)
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Development settings
    debug: bool = True
    reload: bool = True
    environment: str = "development"
    log_level: str = "DEBUG"

    # Allow all origins for development
    cors_origins: list[str] = ["*"]
    allowed_hosts: list[str] = ["*"]


# Development settings instance
dev_settings = DevSettings()
