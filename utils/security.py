"""Security utilities."""

import hashlib
import shlex

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    magic = None
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from loguru import logger

from config import settings


class FileValidator:
    """File validation utilities."""

    ALLOWED_MIME_TYPES = {".jmx": ["application/xml", "text/xml", "text/plain"]}

    DANGEROUS_PATTERNS = [
        b"<script",
        b"javascript:",
        b"vbscript:",
        b"onload=",
        b"onerror=",
        b"eval(",
        b"exec(",
        b"__import__",
        b"subprocess",
        b"os.system",
    ]

    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """Validate file extension."""
        suffix = Path(filename).suffix.lower()
        return suffix in settings.allowed_file_extensions

    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size."""
        return file_size <= settings.upload_max_size

    @classmethod
    def validate_mime_type(cls, file_path: Path) -> bool:
        """Validate MIME type using python-magic."""
        if not HAS_MAGIC:
            logger.warning("python-magic not available, skipping MIME type validation")
            return True  # Skip validation if magic is not available

        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            suffix = file_path.suffix.lower()
            allowed_types = cls.ALLOWED_MIME_TYPES.get(suffix, [])
            return mime_type in allowed_types
        except Exception as e:
            logger.error(f"MIME type validation failed: {e}")
            return False

    @classmethod
    def scan_for_malicious_content(cls, file_path: Path) -> bool:
        """Scan file for potentially malicious content."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                content_lower = content.lower()

                for pattern in cls.DANGEROUS_PATTERNS:
                    if pattern in content_lower:
                        logger.warning(f"Dangerous pattern found in {file_path}: {pattern}")
                        return False
            return True
        except Exception as e:
            logger.error(f"Malicious content scan failed: {e}")
            return False

    @classmethod
    def validate_xml_structure(cls, file_path: Path) -> bool:
        """Validate XML structure for JMX files."""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(file_path)
            root = tree.getroot()

            # Basic JMX structure validation
            if root.tag != "jmeterTestPlan":
                logger.warning(f"Invalid JMX structure in {file_path}")
                return False

            return True
        except ET.ParseError as e:
            logger.error(f"XML parsing failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"XML validation failed: {e}")
            return False

    @classmethod
    async def validate_upload_file(cls, upload_file: UploadFile) -> tuple[bool, Optional[str]]:
        """Comprehensive file validation."""
        # Check filename
        if not upload_file.filename:
            return False, "No filename provided"

        # Check extension
        if not cls.validate_file_extension(upload_file.filename):
            return False, f"File extension not allowed. Allowed: {settings.allowed_file_extensions}"

        # Check file size
        file_size = 0
        content = await upload_file.read()
        file_size = len(content)
        await upload_file.seek(0)  # Reset file pointer

        if not cls.validate_file_size(file_size):
            return False, f"File too large. Max size: {settings.upload_max_size} bytes"

        # Save to temp file for further validation
        temp_path = settings.jmx_files_path / f"temp_{upload_file.filename}"
        try:
            with open(temp_path, "wb") as temp_file:
                temp_file.write(content)

            # MIME type validation
            if not cls.validate_mime_type(temp_path):
                return False, "Invalid file type"

            # Malicious content scan
            if not cls.scan_for_malicious_content(temp_path):
                return False, "File contains potentially malicious content"

            # XML structure validation for JMX files
            if temp_path.suffix.lower() == ".jmx":
                if not cls.validate_xml_structure(temp_path):
                    return False, "Invalid JMX file structure"

            return True, None

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()


class CommandSanitizer:
    """Command sanitization utilities."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove any path components
        filename = Path(filename).name

        # Remove or replace dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[: 255 - len(ext)] + ext

        return filename

    @staticmethod
    def build_safe_command(base_command: str, args: List[str]) -> List[str]:
        """Build safe command with properly escaped arguments."""
        command_parts = [base_command]

        for arg in args:
            # Use shlex.quote to properly escape arguments
            command_parts.append(shlex.quote(str(arg)))

        return command_parts

    @staticmethod
    def validate_path(path: Path, allowed_base: Path) -> bool:
        """Validate that path is within allowed base directory."""
        try:
            resolved_path = path.resolve()
            resolved_base = allowed_base.resolve()
            return str(resolved_path).startswith(str(resolved_base))
        except Exception:
            return False


def generate_file_hash(file_path: Path) -> str:
    """Generate SHA256 hash of file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def generate_secure_filename(original_filename: str) -> str:
    """Generate secure filename with timestamp and hash."""
    import uuid
    from datetime import datetime

    # Sanitize original filename
    safe_name = CommandSanitizer.sanitize_filename(original_filename)
    name, ext = Path(safe_name).stem, Path(safe_name).suffix

    # Generate unique identifier
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]

    return f"{name}_{timestamp}_{unique_id}{ext}"
