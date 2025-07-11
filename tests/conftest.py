"""Test configuration."""

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"

from database import get_db
from dev_server import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override database dependency if it exists
if hasattr(app, "dependency_overrides"):
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Create test directories
    import pathlib

    for directory in ["jmx_files", "jtl_files", "reports", "static", "templates"]:
        pathlib.Path(directory).mkdir(exist_ok=True)

    yield

    # Cleanup test database
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


def wait_for_task_completion(client, task_id, timeout=10, check_interval=0.1):
    """Wait for a task to complete with polling."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = client.get(f"/tasks/{task_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                task_status = data["data"].get("status")
                if task_status in ["completed", "failed"]:
                    return data["data"]

        time.sleep(check_interval)

    raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
