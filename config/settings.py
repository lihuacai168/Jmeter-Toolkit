"""Application configuration management."""

import os
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Basic settings
    app_name: str = "JMeter Toolkit"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "production"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # File storage settings
    jmx_files_path: Path = Path("jmx_files")
    jtl_files_path: Path = Path("jtl_files")
    reports_path: Path = Path("reports")
    upload_max_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_extensions: list[str] = [".jmx"]

    # Database settings
    database_url: str = "postgresql://jmeter:jmeter@localhost:5432/jmeter_toolkit"
    database_echo: bool = False

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # JMeter settings
    jmeter_version: str = "5.5"
    jmeter_home: Optional[str] = None
    jmeter_max_heap: str = "2g"
    jmeter_timeout: int = 3600  # 1 hour

    # Security settings
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[str] = ["*"]
    secret_key: str = "your-secret-key-change-in-production"

    # Monitoring settings
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    @field_validator("jmx_files_path", "jtl_files_path", "reports_path", mode="before")
    @classmethod
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("jmeter_home", mode="before")
    @classmethod
    def set_jmeter_home(cls, v, info):
        """Set JMeter home path."""
        if v is None:
            # Access other field values from info.data
            version = info.data.get("jmeter_version", "5.5") if info.data else "5.5"
            return f"/opt/apache-jmeter-{version}"
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


# Global settings instance
settings = Settings()
