"""Enhanced API tests with real upload/download logic."""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient


def create_test_jmx_content():
    """Create test JMX file content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP Request">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">httpbin.org</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/get</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""


class TestFileUploadDownload:
    """Test file upload and download functionality."""

    def test_upload_valid_jmx_file(self, client: TestClient):
        """Test uploading a valid JMX file."""
        jmx_content = create_test_jmx_content()

        # Create file-like object
        file_data = BytesIO(jmx_content.encode())

        response = client.post("/upload", files={"file": ("test_plan.jmx", file_data, "application/xml")})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_name" in data["data"]
        assert "file_size" in data["data"]
        assert "file_path" in data["data"]
        assert data["data"]["file_name"].endswith(".jmx")
        expected_size = len(jmx_content.encode())
        assert data["data"]["file_size"] == expected_size

        # Verify file actually exists on disk
        file_path = Path(data["data"]["file_path"])
        assert file_path.exists() is True
        assert file_path.stat().st_size == expected_size

        # Verify file content is exactly the same
        with open(file_path, "r") as f:
            saved_content = f.read()
            assert saved_content == jmx_content

    def test_upload_invalid_file_type(self, client: TestClient):
        """Test uploading invalid file type."""
        file_data = BytesIO(b"This is not a JMX file")

        response = client.post("/upload", files={"file": ("test.txt", file_data, "text/plain")})

        assert response.status_code == 400
        assert response.json()["detail"] == "Only JMX files allowed"

    def test_upload_and_execute_workflow(self, client: TestClient):
        """Test complete upload and execute workflow."""
        jmx_content = create_test_jmx_content()
        file_data = BytesIO(jmx_content.encode())

        response = client.post("/upload-and-execute", files={"file": ("test_workflow.jmx", file_data, "application/xml")})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "upload" in data["data"]
        assert "execution" in data["data"]

        # Check upload data
        upload_data = data["data"]["upload"]
        assert "file_name" in upload_data
        assert upload_data["file_name"].endswith(".jmx")

        # Check execution data
        execution_data = data["data"]["execution"]
        assert execution_data["status"] == "completed"
        assert "output_file" in execution_data
        assert execution_data["output_file"].endswith(".jtl")

        # Verify both files exist
        jmx_path = Path(upload_data["file_path"])
        jtl_path = Path("jtl_files") / execution_data["output_file"]
        assert jmx_path.exists()
        assert jtl_path.exists()

        # Verify JTL content structure (supports both CSV and XML formats)
        with open(jtl_path, "r") as f:
            jtl_content = f.read()
            lines = jtl_content.strip().split("\n")
            assert len(lines) >= 2  # Should have content

            # Check if it's CSV format (real JMeter) or XML format (dummy execution)
            if "timeStamp" in lines[0]:
                # CSV format - check headers and data
                assert "elapsed" in lines[0]
                assert "responseCode" in lines[0]
                assert any("200" in line for line in lines[1:])  # At least one 200 response
            elif "<?xml" in lines[0]:
                # XML format (dummy execution) - check for success indicators
                assert "testResults" in jtl_content
                assert 's="true"' in jtl_content or 'rc="200"' in jtl_content
            else:
                # Unknown format
                assert False, f"Unexpected JTL format: {lines[0]}"

    def test_download_jmx_file(self, client: TestClient):
        """Test downloading JMX file."""
        # First upload a file
        jmx_content = create_test_jmx_content()
        file_data = BytesIO(jmx_content.encode())

        upload_response = client.post("/upload", files={"file": ("test_download.jmx", file_data, "application/xml")})

        assert upload_response.status_code == 200
        upload_data = upload_response.json()["data"]
        file_name = upload_data["file_name"]

        # Now download the file
        download_response = client.get(f"/download/jmx/{file_name}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"

        # Verify downloaded content matches original exactly
        downloaded_content = download_response.content.decode()
        assert downloaded_content == jmx_content

    def test_download_jtl_file(self, client: TestClient):
        """Test downloading JTL file."""
        # First upload and execute to create JTL file
        jmx_content = create_test_jmx_content()
        file_data = BytesIO(jmx_content.encode())

        execute_response = client.post(
            "/upload-and-execute", files={"file": ("test_jtl_download.jmx", file_data, "application/xml")}
        )

        assert execute_response.status_code == 200
        execution_data = execute_response.json()["data"]["execution"]
        jtl_filename = execution_data["output_file"]

        # Download the JTL file
        download_response = client.get(f"/download/jtl/{jtl_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"

        # Verify JTL content structure (supports both CSV and XML formats)
        downloaded_content = download_response.content.decode()
        lines = downloaded_content.strip().split("\n")
        assert len(lines) >= 2  # Should have content

        # Check if it's CSV format (real JMeter) or XML format (dummy execution)
        if "timeStamp" in lines[0]:
            # CSV format - check headers and data
            assert "elapsed" in lines[0]
            assert "responseCode" in lines[0]
            assert any("200" in line for line in lines[1:])  # At least one 200 response
        elif "<?xml" in lines[0]:
            # XML format (dummy execution) - check for success indicators
            assert "testResults" in downloaded_content
            assert 's="true"' in downloaded_content or 'rc="200"' in downloaded_content
        else:
            # Unknown format
            assert False, f"Unexpected JTL format: {lines[0]}"

    def test_download_nonexistent_file(self, client: TestClient):
        """Test downloading non-existent file."""
        response = client.get("/download/jmx/nonexistent.jmx")
        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"

    def test_download_invalid_file_type(self, client: TestClient):
        """Test downloading with invalid file type."""
        response = client.get("/download/invalid/test.txt")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid file type"


class TestFileListingIntegration:
    """Test file listing with actual files."""

    def test_list_files_after_upload(self, client: TestClient):
        """Test file listing after uploading files."""
        import uuid

        # Create unique test identifier
        test_id = str(uuid.uuid4())[:8]
        uploaded_filenames = []

        # Upload multiple files with unique names
        for i in range(3):
            jmx_content = create_test_jmx_content()
            file_data = BytesIO(jmx_content.encode())

            filename = f"test_list_{test_id}_{i}.jmx"
            response = client.post("/upload", files={"file": (filename, file_data, "application/xml")})
            assert response.status_code == 200
            uploaded_filenames.append(response.json()["data"]["file_name"])

        # List JMX files
        response = client.get("/files?file_type=jmx")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify exact count of our uploaded files
        our_files = [f for f in data["data"]["files"] if f["name"] in uploaded_filenames]
        assert len(our_files) == 3

        for file_info in our_files:
            assert "name" in file_info
            assert "size" in file_info
            assert "modified" in file_info
            assert "path" in file_info
            assert file_info["name"].endswith(".jmx") is True
            # Verify exact file size matches JMX content
            expected_size = len(create_test_jmx_content().encode())
            assert file_info["size"] == expected_size

    def test_list_jtl_files_after_execution(self, client: TestClient):
        """Test listing JTL files after execution."""
        import uuid

        # Create unique test identifier
        test_id = str(uuid.uuid4())[:8]
        created_jtl_files = []

        # Upload and execute files to create JTL files
        for i in range(2):
            jmx_content = create_test_jmx_content()
            file_data = BytesIO(jmx_content.encode())

            filename = f"test_exec_{test_id}_{i}.jmx"
            response = client.post("/upload-and-execute", files={"file": (filename, file_data, "application/xml")})
            assert response.status_code == 200
            # Track the created JTL filename
            jtl_filename = response.json()["data"]["execution"]["output_file"]
            created_jtl_files.append(jtl_filename)

        # List JTL files
        response = client.get("/files?file_type=jtl")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify exact count of our JTL files created
        our_jtl_files = [f for f in data["data"]["files"] if f["name"] in created_jtl_files]
        assert len(our_jtl_files) == 2

        # Verify JTL file details
        for file_info in our_jtl_files:
            assert file_info["name"].endswith(".jtl") is True
            # JTL files should have reasonable size (CSV format with headers and data)
            assert file_info["size"] > 50  # Should contain at least headers and some data
            assert file_info["size"] < 10000  # Should not be unreasonably large for test data


class TestTaskManagementIntegration:
    """Test task management with actual workflow."""

    def test_task_creation_and_retrieval(self, client: TestClient):
        """Test task creation and retrieval."""
        # Execute a file to create a task
        jmx_content = create_test_jmx_content()
        file_data = BytesIO(jmx_content.encode())

        execute_response = client.post("/upload-and-execute", files={"file": ("test_task.jmx", file_data, "application/xml")})

        assert execute_response.status_code == 200
        task_data = execute_response.json()["data"]["execution"]
        task_id = task_data["task_id"]

        # Retrieve specific task
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.status_code == 200

        retrieved_task = task_response.json()["data"]
        assert retrieved_task["task_id"] == task_id
        assert retrieved_task["status"] == "completed"
        assert "output_file" in retrieved_task

        # List all tasks
        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200

        tasks_data = tasks_response.json()["data"]
        # Verify we have at least our created task
        task_ids = [t["task_id"] for t in tasks_data["tasks"]]
        assert task_id in task_ids

        # Find our task in the list
        our_task = next((t for t in tasks_data["tasks"] if t["task_id"] == task_id), None)
        assert our_task is not None
        assert our_task["status"] == "completed"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_empty_file_upload(self, client: TestClient):
        """Test uploading empty file."""
        file_data = BytesIO(b"")

        response = client.post("/upload", files={"file": ("empty.jmx", file_data, "application/xml")})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # File should still be created even if empty
        assert data["data"]["file_size"] == 0

    def test_large_file_handling(self, client: TestClient):
        """Test handling of large files."""
        # Create a large JMX content (repeat the test plan content)
        base_content = create_test_jmx_content()
        large_content = base_content * 100  # Make it larger

        file_data = BytesIO(large_content.encode())

        response = client.post("/upload", files={"file": ("large_test.jmx", file_data, "application/xml")})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        expected_large_size = len(large_content.encode())
        assert data["data"]["file_size"] == expected_large_size

        # Verify file can be downloaded
        file_name = data["data"]["file_name"]
        download_response = client.get(f"/download/jmx/{file_name}")
        assert download_response.status_code == 200

        downloaded_size = len(download_response.content)
        assert downloaded_size == data["data"]["file_size"]

    def test_execute_nonexistent_file(self, client: TestClient):
        """Test executing non-existent file."""
        response = client.post("/execute", json={"file_name": "nonexistent.jmx"})
        assert response.status_code == 404
        assert response.json()["detail"] == "JMX file not found"

    def test_special_characters_in_filename(self, client: TestClient):
        """Test handling of special characters in filename."""
        jmx_content = create_test_jmx_content()
        file_data = BytesIO(jmx_content.encode())

        # File with special characters
        response = client.post(
            "/upload", files={"file": ("test file with spaces & symbols!.jmx", file_data, "application/xml")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Filename should be sanitized
        safe_filename = data["data"]["file_name"]
        assert safe_filename.endswith(".jmx")
        # Should still be downloadable
        download_response = client.get(f"/download/jmx/{safe_filename}")
        assert download_response.status_code == 200
