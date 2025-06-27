"""Security tests."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from utils.security import CommandSanitizer, FileValidator, generate_secure_filename


class TestFileValidator:
    """Test file validator."""

    def test_validate_file_extension_valid(self):
        """Test valid file extension."""
        assert FileValidator.validate_file_extension("test.jmx") is True

    def test_validate_file_extension_invalid(self):
        """Test invalid file extension."""
        assert FileValidator.validate_file_extension("test.txt") is False
        assert FileValidator.validate_file_extension("test.exe") is False

    def test_validate_file_size_valid(self):
        """Test valid file size."""
        assert FileValidator.validate_file_size(1024) is True

    def test_validate_file_size_invalid(self):
        """Test invalid file size."""
        assert FileValidator.validate_file_size(200 * 1024 * 1024) is False

    def test_scan_for_malicious_content(self, tmp_path):
        """Test malicious content scanning."""
        # Create safe file
        safe_file = tmp_path / "safe.jmx"
        safe_file.write_text("<?xml version='1.0' encoding='UTF-8'?><jmeterTestPlan></jmeterTestPlan>")
        assert FileValidator.scan_for_malicious_content(safe_file) is True

        # Create malicious file
        malicious_file = tmp_path / "malicious.jmx"
        malicious_file.write_text("<script>alert('xss')</script>")
        assert FileValidator.scan_for_malicious_content(malicious_file) is False


class TestCommandSanitizer:
    """Test command sanitizer."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert CommandSanitizer.sanitize_filename("test.jmx") == "test.jmx"
        assert CommandSanitizer.sanitize_filename("../../../etc/passwd") == "passwd"
        assert CommandSanitizer.sanitize_filename("test<script>.jmx") == "test_script_.jmx"

    def test_build_safe_command(self):
        """Test safe command building."""
        command = CommandSanitizer.build_safe_command("jmeter", ["-n", "-t", "test file.jmx"])
        assert "jmeter" in command
        assert "'test file.jmx'" in " ".join(command)

    def test_validate_path(self, tmp_path):
        """Test path validation."""
        allowed_base = tmp_path / "allowed"
        allowed_base.mkdir()

        # Valid path
        valid_path = allowed_base / "test.jmx"
        assert CommandSanitizer.validate_path(valid_path, allowed_base) is True

        # Invalid path (outside base)
        invalid_path = tmp_path / "not_allowed" / "test.jmx"
        assert CommandSanitizer.validate_path(invalid_path, allowed_base) is False


def test_generate_secure_filename():
    """Test secure filename generation."""
    original = "test file.jmx"
    secure = generate_secure_filename(original)

    assert secure.endswith(".jmx")
    # The function sanitizes spaces to underscores, so check for the base name pattern
    assert "test" in secure
    assert len(secure) > len(original)  # Should have timestamp and UUID
    # Check for timestamp pattern (YYYYMMDD_HHMMSS)
    import re

    assert re.search(r"\d{8}_\d{6}", secure) is not None
