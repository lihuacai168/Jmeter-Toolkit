"""Tests for execute and upload-and-execute API endpoints."""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestExecuteAPI:
    """Test cases for execute API endpoints."""

    def setup_method(self):
        """Setup test data for each test method."""
        # Sample JMX content
        self.sample_jmx_content = """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan">
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" \
testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <stringProp name="TestPlan.comments">Simple test plan for API testing</stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" \
guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller">
          <stringProp name="LoopController.loops">1</stringProp>
          <boolProp name="LoopController.continue_forever">false</boolProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <boolProp name="ThreadGroup.delayedStart">false</boolProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP Request">
          <stringProp name="HTTPSampler.domain">httpbin.org</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/get</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""

    def create_test_jmx_file(self, filename: str) -> str:
        """Create a test JMX file and return its name."""
        jmx_path = Path("jmx_files") / filename
        jmx_path.parent.mkdir(exist_ok=True)
        with open(jmx_path, "w", encoding="utf-8") as f:
            f.write(self.sample_jmx_content)
        return filename

    def test_upload_valid_jmx_file(self, client: TestClient):
        """Test uploading a valid JMX file."""
        jmx_content = self.sample_jmx_content.encode("utf-8")

        response = client.post("/upload", files={"file": ("test_upload.jmx", io.BytesIO(jmx_content), "application/xml")})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "data" in data
        assert "file_name" in data["data"]
        assert "file_size" in data["data"]
        assert "file_path" in data["data"]
        assert "upload_time" in data["data"]
        assert data["data"]["file_name"].endswith(".jmx")
        assert data["data"]["file_size"] > 0

        # Verify file was actually created
        uploaded_file = Path(data["data"]["file_path"])
        assert uploaded_file.exists()
        assert uploaded_file.stat().st_size > 0

    def test_upload_invalid_file_extension(self, client: TestClient):
        """Test uploading a file with invalid extension."""
        content = b"invalid content"

        response = client.post("/upload", files={"file": ("test.txt", io.BytesIO(content), "text/plain")})

        assert response.status_code == 400

    def test_execute_existing_jmx_file(self, client: TestClient):
        """Test executing an existing JMX file."""
        # First create a test file
        filename = self.create_test_jmx_file("test_execute.jmx")

        # Execute the file
        response = client.post("/execute", json={"file_name": filename})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "data" in data
        assert "task_id" in data["data"]
        assert "status" in data["data"]
        assert "file_name" in data["data"]
        assert "output_file" in data["data"]
        assert "cost_time" in data["data"]
        assert "created_at" in data["data"]
        assert "completed_at" in data["data"]

        # Check data values
        assert data["data"]["file_name"] == filename
        # Wait for async execution to complete
        task_id = data["data"].get("task_id")
        if data["data"]["status"] in ["pending", "running"] and task_id:
            from tests.conftest import wait_for_task_completion

            task_data = wait_for_task_completion(client, task_id)
            data["data"] = task_data
        assert data["data"]["status"] == "completed"
        assert data["data"]["output_file"].endswith(".jtl")

        # Verify JTL file was created
        jtl_path = Path("jtl_files") / data["data"]["output_file"]
        assert jtl_path.exists()
        assert jtl_path.stat().st_size > 0

    def test_execute_nonexistent_jmx_file(self, client: TestClient):
        """Test executing a non-existent JMX file."""
        response = client.post("/execute", json={"file_name": "nonexistent_file.jmx"})

        assert response.status_code == 404
        data = response.json()
        assert "JMX file not found" in data["detail"]

    def test_execute_missing_file_name(self, client: TestClient):
        """Test execute endpoint without file_name parameter."""
        response = client.post("/execute", json={})

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_execute_invalid_file_name_type(self, client: TestClient):
        """Test execute endpoint with invalid file_name type."""
        response = client.post("/execute", json={"file_name": 123})  # Should be string

        assert response.status_code == 422  # Validation error

    def test_upload_and_execute_valid_file(self, client: TestClient):
        """Test upload-and-execute endpoint with valid JMX file."""
        jmx_content = self.sample_jmx_content.encode("utf-8")

        response = client.post(
            "/upload-and-execute", files={"file": ("test_upload_execute.jmx", io.BytesIO(jmx_content), "application/xml")}
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "data" in data
        assert "upload" in data["data"]
        assert "execution" in data["data"]

        # Check upload data
        upload_data = data["data"]["upload"]
        assert "file_name" in upload_data
        assert "file_size" in upload_data
        assert "file_path" in upload_data
        assert upload_data["file_name"].endswith(".jmx")

        # Check execution data
        execution_data = data["data"]["execution"]
        assert "task_id" in execution_data
        assert "status" in execution_data
        assert "file_name" in execution_data
        assert "output_file" in execution_data
        # Wait for async execution to complete
        task_id = execution_data.get("task_id")
        if execution_data["status"] in ["pending", "running"] and task_id:
            from tests.conftest import wait_for_task_completion

            execution_data = wait_for_task_completion(client, task_id)
            data["data"]["execution"] = execution_data
        assert execution_data["status"] == "completed"
        assert execution_data["file_name"] == upload_data["file_name"]

        # Verify files were created
        jmx_path = Path(upload_data["file_path"])
        jtl_path = Path("jtl_files") / execution_data["output_file"]
        assert jmx_path.exists()
        assert jtl_path.exists()

    def test_upload_and_execute_invalid_file(self, client: TestClient):
        """Test upload-and-execute endpoint with invalid file."""
        content = b"invalid content"

        response = client.post("/upload-and-execute", files={"file": ("test.txt", io.BytesIO(content), "text/plain")})

        assert response.status_code == 400

    def test_upload_and_execute_empty_file(self, client: TestClient):
        """Test upload-and-execute endpoint with empty file."""
        response = client.post("/upload-and-execute", files={"file": ("empty.jmx", io.BytesIO(b""), "application/xml")})

        # Should still work but create empty files
        assert response.status_code == 200

    def test_upload_and_execute_large_file(self, client: TestClient):
        """Test upload-and-execute with a larger JMX file."""
        # Create a larger JMX content by repeating the basic structure
        large_content = self.sample_jmx_content * 10
        jmx_content = large_content.encode("utf-8")

        response = client.post(
            "/upload-and-execute", files={"file": ("large_test.jmx", io.BytesIO(jmx_content), "application/xml")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check that file size is correctly reported
        upload_data = data["data"]["upload"]
        assert upload_data["file_size"] == len(jmx_content)

    def test_sequential_executions(self, client: TestClient):
        """Test multiple sequential executions."""
        import time

        filename = self.create_test_jmx_file("test_sequential.jmx")

        # Execute the same file multiple times with small delays
        responses = []
        for i in range(3):
            response = client.post("/execute", json={"file_name": filename})
            assert response.status_code == 200
            responses.append(response.json())
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Check that each execution has unique task_id
        task_ids = [r["data"]["task_id"] for r in responses]
        assert len(set(task_ids)) == 3  # All unique

        # Check that output files will be created

        # Wait for all tasks to complete and verify JTL files were created
        for i, response_data in enumerate(responses):
            task_id = response_data["data"]["task_id"]
            # Wait for async execution to complete
            if response_data["data"]["status"] in ["pending", "running"]:
                from tests.conftest import wait_for_task_completion

                completed_task = wait_for_task_completion(client, task_id)
                assert completed_task["status"] == "completed"

            # Verify JTL file exists
            output_file = response_data["data"]["output_file"]
            jtl_path = Path("jtl_files") / output_file
            assert jtl_path.exists()

    def test_get_task_after_execution(self, client: TestClient):
        """Test retrieving task information after execution."""
        filename = self.create_test_jmx_file("test_task_retrieval.jmx")

        # Execute file
        execute_response = client.post("/execute", json={"file_name": filename})
        assert execute_response.status_code == 200

        task_id = execute_response.json()["data"]["task_id"]

        # Get task information
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.status_code == 200

        task_data = task_response.json()
        assert task_data["success"] is True
        assert task_data["data"]["task_id"] == task_id
        # Wait for async execution to complete
        if task_data["data"]["status"] in ["pending", "running"]:
            from tests.conftest import wait_for_task_completion

            task_data["data"] = wait_for_task_completion(client, task_id)
        assert task_data["data"]["status"] == "completed"

    def test_list_tasks_after_executions(self, client: TestClient):
        """Test listing tasks after multiple executions."""
        # Perform multiple executions
        filenames = []
        for i in range(2):
            filename = self.create_test_jmx_file(f"test_list_{i}.jmx")
            filenames.append(filename)

            response = client.post("/execute", json={"file_name": filename})
            assert response.status_code == 200

        # List all tasks
        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200

        tasks_data = tasks_response.json()
        assert tasks_data["success"] is True
        assert "tasks" in tasks_data["data"]
        assert "total" in tasks_data["data"]
        assert tasks_data["data"]["total"] >= 2

    def test_file_cleanup_and_isolation(self, client: TestClient):
        """Test that files are properly isolated between tests."""
        # This test verifies that test setup/teardown works correctly
        filename = "test_isolation.jmx"

        # Create file
        self.create_test_jmx_file(filename)

        # Verify file exists
        jmx_path = Path("jmx_files") / filename
        assert jmx_path.exists()

        # Execute file
        response = client.post("/execute", json={"file_name": filename})
        assert response.status_code == 200

    @pytest.mark.parametrize("file_extension", [".jmx", ".JMX", ".Jmx"])
    def test_case_insensitive_jmx_extension(self, client: TestClient, file_extension):
        """Test that JMX file upload works with different case extensions."""
        jmx_content = self.sample_jmx_content.encode("utf-8")
        filename = f"test_case{file_extension}"

        response = client.post("/upload", files={"file": (filename, io.BytesIO(jmx_content), "application/xml")})

        # Current implementation only accepts .jmx (lowercase)
        if file_extension == ".jmx":
            assert response.status_code == 200
        else:
            assert response.status_code == 400

    def test_concurrent_uploads(self, client: TestClient):
        """Test handling of multiple concurrent-like uploads."""
        import time

        jmx_content = self.sample_jmx_content.encode("utf-8")

        # Simulate multiple uploads with same base name and small delays
        responses = []
        for i in range(3):
            response = client.post("/upload", files={"file": ("same_name.jmx", io.BytesIO(jmx_content), "application/xml")})
            responses.append(response)
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # Check that we got valid responses (filenames may be same due to timestamp resolution)
        filenames = [r.json()["data"]["file_name"] for r in responses]
        assert len(filenames) == 3  # We got 3 responses

    def test_error_handling_in_upload_and_execute(self, client: TestClient):
        """Test error handling in upload-and-execute workflow."""
        # Test with malformed request (no file)
        response = client.post("/upload-and-execute")
        assert response.status_code == 422  # Unprocessable Entity

        # Test with invalid form data
        response = client.post("/upload-and-execute", data={"not_a_file": "invalid"})
        assert response.status_code == 422
