"""Performance tests for execute API endpoints."""

import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient


class TestExecutePerformance:
    """Performance tests for execute API endpoints."""

    def setup_method(self):
        """Setup test data."""
        self.sample_jmx_content = """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Performance Test Plan">
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" \
testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <stringProp name="TestPlan.comments">Performance test plan</stringProp>
    </TestPlan>
    <hashTree/>
  </hashTree>
</jmeterTestPlan>"""

    @pytest.mark.performance
    def test_upload_response_time(self, client: TestClient):
        """Test upload endpoint response time."""
        jmx_content = self.sample_jmx_content.encode("utf-8")

        start_time = time.time()
        response = client.post("/upload", files={"file": ("perf_test.jmx", io.BytesIO(jmx_content), "application/xml")})
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Upload should complete within 2 seconds
        assert response_time < 2.0, f"Upload took {response_time:.2f}s, expected < 2.0s"

    @pytest.mark.performance
    def test_execute_response_time(self, client: TestClient):
        """Test execute endpoint response time."""
        # First upload a file
        jmx_content = self.sample_jmx_content.encode("utf-8")
        upload_response = client.post(
            "/upload", files={"file": ("perf_execute.jmx", io.BytesIO(jmx_content), "application/xml")}
        )
        assert upload_response.status_code == 200
        file_name = upload_response.json()["data"]["file_name"]

        # Test execute response time
        start_time = time.time()
        response = client.post("/execute", json={"file_name": file_name})
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Execute should complete within 1 second (simulated)
        assert response_time < 1.0, f"Execute took {response_time:.2f}s, expected < 1.0s"

    @pytest.mark.performance
    def test_upload_and_execute_response_time(self, client: TestClient):
        """Test upload-and-execute endpoint response time."""
        jmx_content = self.sample_jmx_content.encode("utf-8")

        start_time = time.time()
        response = client.post(
            "/upload-and-execute", files={"file": ("perf_upload_execute.jmx", io.BytesIO(jmx_content), "application/xml")}
        )
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Combined operation should complete within 3 seconds
        assert response_time < 3.0, f"Upload-and-execute took {response_time:.2f}s, expected < 3.0s"

    @pytest.mark.performance
    def test_concurrent_uploads(self, client: TestClient):
        """Test concurrent upload performance."""
        jmx_content = self.sample_jmx_content.encode("utf-8")
        num_concurrent = 5

        def upload_file(index):
            """Upload a single file."""
            start_time = time.time()
            response = client.post(
                "/upload", files={"file": (f"concurrent_{index}.jmx", io.BytesIO(jmx_content), "application/xml")}
            )
            end_time = time.time()
            return response, end_time - start_time

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_file, i) for i in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time

        # All uploads should succeed
        for response, _ in results:
            assert response.status_code == 200

        # Total time should be reasonable (not linear with number of requests)
        assert total_time < num_concurrent * 2, f"Concurrent uploads took {total_time:.2f}s"

        # Individual response times should be reasonable
        response_times = [rt for _, rt in results]
        max_response_time = max(response_times)
        assert max_response_time < 5.0, f"Slowest upload took {max_response_time:.2f}s"

    @pytest.mark.performance
    def test_concurrent_executions(self, client: TestClient):
        """Test concurrent execution performance."""
        jmx_content = self.sample_jmx_content.encode("utf-8")
        num_concurrent = 3

        # First, upload files for execution
        uploaded_files = []
        for i in range(num_concurrent):
            response = client.post("/upload", files={"file": (f"exec_{i}.jmx", io.BytesIO(jmx_content), "application/xml")})
            assert response.status_code == 200
            uploaded_files.append(response.json()["data"]["file_name"])

        def execute_file(file_name):
            """Execute a single file."""
            start_time = time.time()
            response = client.post("/execute", json={"file_name": file_name})
            end_time = time.time()
            return response, end_time - start_time

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(execute_file, fn) for fn in uploaded_files]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time

        # All executions should succeed
        for response, _ in results:
            assert response.status_code == 200

        # Total time should be reasonable
        assert total_time < num_concurrent * 3, f"Concurrent executions took {total_time:.2f}s"

    @pytest.mark.performance
    def test_large_file_upload(self, client: TestClient):
        """Test upload performance with larger files."""
        # Create a larger JMX file (repeat content multiple times)
        large_content = self.sample_jmx_content * 100  # About 100KB
        jmx_content = large_content.encode("utf-8")

        start_time = time.time()
        response = client.post("/upload", files={"file": ("large_file.jmx", io.BytesIO(jmx_content), "application/xml")})
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Large file upload should still be reasonably fast
        assert response_time < 5.0, f"Large file upload took {response_time:.2f}s, expected < 5.0s"

        # Verify file size is correct
        file_size = response.json()["data"]["file_size"]
        assert file_size == len(jmx_content)

    @pytest.mark.performance
    def test_memory_usage_multiple_operations(self, client: TestClient):
        """Test memory usage doesn't grow excessively with multiple operations."""
        jmx_content = self.sample_jmx_content.encode("utf-8")
        num_operations = 10

        # Perform multiple upload-and-execute operations
        for i in range(num_operations):
            response = client.post(
                "/upload-and-execute", files={"file": (f"memory_test_{i}.jmx", io.BytesIO(jmx_content), "application/xml")}
            )
            assert response.status_code == 200

        # Test that we can still perform operations efficiently
        start_time = time.time()
        response = client.post(
            "/upload-and-execute", files={"file": ("final_test.jmx", io.BytesIO(jmx_content), "application/xml")}
        )
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Final operation should still be fast
        assert response_time < 3.0, f"Final operation took {response_time:.2f}s after {num_operations} operations"

    @pytest.mark.performance
    def test_api_endpoint_response_times(self, client: TestClient):
        """Test response times of various API endpoints."""
        # Upload a file first
        jmx_content = self.sample_jmx_content.encode("utf-8")
        upload_response = client.post(
            "/upload", files={"file": ("api_perf_test.jmx", io.BytesIO(jmx_content), "application/xml")}
        )
        assert upload_response.status_code == 200

        # Execute file to create task
        file_name = upload_response.json()["data"]["file_name"]
        execute_response = client.post("/execute", json={"file_name": file_name})
        assert execute_response.status_code == 200
        task_id = execute_response.json()["data"]["task_id"]

        # Test various endpoint response times
        endpoints = [
            ("/health", "GET", None),
            ("/tasks", "GET", None),
            (f"/tasks/{task_id}", "GET", None),
            ("/files?file_type=jmx", "GET", None),
            ("/files?file_type=jtl", "GET", None),
        ]

        for endpoint, method, data in endpoints:
            start_time = time.time()
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=data)
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time

            # All API endpoints should respond within 1 second
            assert response_time < 1.0, f"{endpoint} took {response_time:.2f}s, expected < 1.0s"
