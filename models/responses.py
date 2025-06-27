"""API response models."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response format."""

    success: bool
    message: str
    data: Optional[T] = None
    code: str = "SUCCESS"
    timestamp: Optional[str] = None

    @classmethod
    def success_response(
        cls, data: Optional[T] = None, message: str = "Operation successful", code: str = "SUCCESS"
    ) -> "APIResponse[T]":
        """Create a success response."""
        from datetime import datetime

        return cls(success=True, message=message, data=data, code=code, timestamp=datetime.utcnow().isoformat())

    @classmethod
    def error_response(
        cls, message: str = "Operation failed", code: str = "ERROR", data: Optional[T] = None
    ) -> "APIResponse[T]":
        """Create an error response."""
        from datetime import datetime

        return cls(success=False, message=message, data=data, code=code, timestamp=datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str
    services: dict[str, str]


class TaskResponse(BaseModel):
    """Task execution response."""

    task_id: str
    status: str
    file_name: str
    output_file: Optional[str] = None
    cost_time: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class FileUploadResponse(BaseModel):
    """File upload response."""

    file_name: str
    file_size: int
    file_path: str
    upload_time: str


class ReportResponse(BaseModel):
    """Report generation response."""

    report_id: str
    report_url: str
    jtl_file: str
    generated_at: str
    report_path: str
