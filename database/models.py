"""Database models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class TaskStatus(PyEnum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileType(PyEnum):
    """File type enumeration."""

    JMX = "jmx"
    JTL = "jtl"


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # File information
    jmx_file_name = Column(String(255), nullable=False)
    jmx_file_path = Column(String(500), nullable=False)
    jmx_file_hash = Column(String(64), nullable=True)

    # Output information
    jtl_file_name = Column(String(255), nullable=True)
    jtl_file_path = Column(String(500), nullable=True)
    report_path = Column(String(500), nullable=True)

    # Execution information
    process_id = Column(Integer, nullable=True)
    command = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)

    # Timing information
    cost_time = Column(Float, nullable=True)  # in seconds
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id}, name={self.name}, status={self.status})>"


class FileRecord(Base):
    """File record model."""

    __tablename__ = "file_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=True)

    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<FileRecord(id={self.id}, name={self.original_name}, type={self.file_type})>"


class Report(Base):
    """Report model."""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), nullable=False)
    jtl_file_path = Column(String(500), nullable=False)
    report_path = Column(String(500), nullable=False)
    report_url = Column(String(500), nullable=False)

    # Generation information
    generation_time = Column(Float, nullable=True)  # in seconds
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Metadata
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Report(id={self.id}, task_id={self.task_id})>"


class AuditLog(Base):
    """Audit log model."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
