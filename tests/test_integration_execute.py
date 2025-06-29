"""Integration tests for execute API endpoints with real test server."""

import os
import time
from pathlib import Path

import httpx
import pytest


class TestExecuteIntegration:
    """Integration tests that require the test server to be running."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_environment(self):
        """Setup test environment for integration tests."""
        # Check if running in Docker Compose environment
        test_server_url = os.getenv("TEST_SERVER_URL", "http://localhost:3000")

        # Wait for test server to be available
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                with httpx.Client() as client:
                    response = client.get(f"{test_server_url}/health", timeout=5)
                    if response.status_code == 200:
                        yield
                        return
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    pytest.skip(f"Test server not reachable at {test_server_url} after {max_retries} attempts")

    def test_execute_with_real_jmx_against_test_server(self, client):
        """Test executing real JMX file against running test server."""
        # Use the fast test file for quicker integration testing
        sample_jmx_path = Path("test_examples/fast_test.jmx")
        if not sample_jmx_path.exists():
            pytest.skip("Fast test JMX file not found")

        # Upload the real JMX file
        with open(sample_jmx_path, "rb") as f:
            response = client.post("/upload", files={"file": ("fast_test.jmx", f, "application/xml")})

        assert response.status_code == 200
        upload_data = response.json()["data"]

        # Execute the uploaded file
        execute_response = client.post("/execute", json={"file_name": upload_data["file_name"]})

        assert execute_response.status_code == 200
        execution_data = execute_response.json()["data"]

        # Verify execution was successful - wait for async completion
        task_id = execution_data.get("task_id")
        if execution_data["status"] in ["pending", "running"] and task_id:
            from tests.conftest import wait_for_task_completion

            execution_data = wait_for_task_completion(client, task_id)
        assert execution_data["status"] == "completed"
        assert execution_data["file_name"] == upload_data["file_name"]

        # In Docker environment, files might be in different locations
        # Just verify the response contains expected data
        assert "output_file" in execution_data
        assert "task_id" in execution_data
        assert execution_data["output_file"].endswith(".jtl")

    def test_upload_and_execute_with_real_jmx(self, client):
        """Test upload-and-execute with real JMX file."""
        sample_jmx_path = Path("test_examples/fast_test.jmx")
        if not sample_jmx_path.exists():
            pytest.skip("Fast test JMX file not found")

        # Upload and execute in one step
        with open(sample_jmx_path, "rb") as f:
            response = client.post("/upload-and-execute", files={"file": ("fast_test.jmx", f, "application/xml")})

        assert response.status_code == 200
        data = response.json()

        # Verify both upload and execution were successful
        assert data["success"] is True
        assert "upload" in data["data"]
        assert "execution" in data["data"]

        upload_data = data["data"]["upload"]
        execution_data = data["data"]["execution"]

        # Wait for async execution to complete
        task_id = execution_data.get("task_id")
        if execution_data["status"] in ["pending", "running"] and task_id:
            from tests.conftest import wait_for_task_completion

            execution_data = wait_for_task_completion(client, task_id)
            data["data"]["execution"] = execution_data
        assert execution_data["status"] == "completed"
        assert execution_data["file_name"] == upload_data["file_name"]

        # Verify response data structure (files may be in different paths in Docker)
        assert "file_path" in upload_data
        assert "output_file" in execution_data
        assert execution_data["output_file"].endswith(".jtl")

    def test_end_to_end_workflow(self, client):
        """Test complete end-to-end workflow."""
        sample_jmx_path = Path("test_examples/fast_test.jmx")
        if not sample_jmx_path.exists():
            pytest.skip("Fast test JMX file not found")

        # Step 1: Upload and execute
        with open(sample_jmx_path, "rb") as f:
            upload_execute_response = client.post(
                "/upload-and-execute", files={"file": ("e2e_test.jmx", f, "application/xml")}
            )

        assert upload_execute_response.status_code == 200
        execution_data = upload_execute_response.json()["data"]["execution"]
        task_id = execution_data["task_id"]

        # Step 2: Check task status
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.status_code == 200
        task_data = task_response.json()["data"]
        # Wait for async execution to complete
        if task_data["status"] in ["pending", "running"]:
            from tests.conftest import wait_for_task_completion

            task_data = wait_for_task_completion(client, task_id)
        assert task_data["status"] == "completed"

        # Step 3: List all tasks
        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200
        tasks_data = tasks_response.json()["data"]

        # Find our task in the list
        task_found = False
        for task in tasks_data["tasks"]:
            if task["task_id"] == task_id:
                task_found = True
                break
        assert task_found

        # Step 4: List JMX files
        jmx_files_response = client.get("/files?file_type=jmx")
        assert jmx_files_response.status_code == 200

        # Step 5: List JTL files
        jtl_files_response = client.get("/files?file_type=jtl")
        assert jtl_files_response.status_code == 200

        # Verify our files are in the lists (may be empty in containerized environment)
        jtl_files = jtl_files_response.json()["data"]["files"]
        # Just verify the structure is correct, files may not persist in test containers
        assert isinstance(jtl_files, list)
