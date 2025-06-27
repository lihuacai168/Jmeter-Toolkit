"""API tests."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "status" in data["data"]
    assert "version" in data["data"]
    assert "timestamp" in data


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    # simple_dev doesn't have metrics endpoint, so 404 is expected
    assert response.status_code == 404


def test_list_files_jmx(client: TestClient):
    """Test list JMX files endpoint."""
    response = client.get("/files?file_type=jmx")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "files" in data["data"]


def test_list_files_jtl(client: TestClient):
    """Test list JTL files endpoint."""
    response = client.get("/files?file_type=jtl")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "files" in data["data"]


def test_list_tasks(client: TestClient):
    """Test list tasks endpoint."""
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "tasks" in data["data"]


def test_invalid_file_type(client: TestClient):
    """Test invalid file type parameter."""
    response = client.get("/files?file_type=invalid")
    # simple_dev returns 200 with error in response body
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


def test_task_not_found(client: TestClient):
    """Test get task that doesn't exist."""
    response = client.get("/tasks/invalid-task-id")
    # simple_dev raises HTTPException, so 404 is expected
    assert response.status_code == 404