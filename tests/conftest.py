"""Test configuration."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"

from database import Base, get_db
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
if hasattr(app, 'dependency_overrides'):
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