"""API tests."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "jmeter_toolkit" in response.text


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
    assert response.status_code == 422


def test_task_not_found(client: TestClient):
    """Test get task that doesn't exist."""
    response = client.get("/tasks/invalid-task-id")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False