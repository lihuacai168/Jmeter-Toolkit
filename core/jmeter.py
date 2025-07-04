# !/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from database import FileRecord, FileType, Task, TaskStatus
from utils.security import FileValidator, generate_file_hash, generate_secure_filename
from utils.tasks import execute_jmeter_task, generate_html_report_task


class RunCmdResp:
    pid: int
    stdout: str
    stderr: str
    returncode: int


class ExecuteJmxResponse:
    output_file_path: str
    cost_time: str
    status: str
    output_file: str
    err: str = ""
    run_cmd_resp: RunCmdResp = None


class JMeterManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.jmx_file_path = settings.jmx_files_path
        self.jtl_files_path = settings.jtl_files_path

    async def upload_jmx(self, jmx_file: UploadFile) -> dict:
        """Upload and validate JMX file."""
        # Validate file
        is_valid, error_msg = await FileValidator.validate_upload_file(jmx_file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Generate secure filename
        secure_filename = generate_secure_filename(jmx_file.filename)
        file_path = self.jmx_file_path / secure_filename

        # Read file content
        content = await jmx_file.read()
        file_size = len(content)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Generate file hash
        file_hash = generate_file_hash(file_path)

        # Save file record to database
        file_record = FileRecord(
            original_name=jmx_file.filename,
            stored_name=secure_filename,
            file_path=str(file_path),
            file_type=FileType.JMX,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=jmx_file.content_type,
        )

        self.db.add(file_record)
        self.db.commit()

        logger.info(f"JMX file uploaded successfully: {secure_filename}")

        return {
            "file_id": str(file_record.id),
            "file_name": secure_filename,
            "original_name": jmx_file.filename,
            "file_path": str(file_path.absolute()),
            "file_size": file_size,
            "file_hash": file_hash,
        }

    async def execute_jmx_async(self, file_name: str) -> dict:
        """Execute JMX file asynchronously using Celery."""
        # Find file record
        file_record = (
            self.db.query(FileRecord)
            .filter(FileRecord.stored_name == file_name, FileRecord.file_type == FileType.JMX, FileRecord.is_deleted is False)
            .first()
        )

        if not file_record:
            raise HTTPException(status_code=404, detail="JMX file not found")

        # Check if file exists on disk
        jmx_path = Path(file_record.file_path)
        if not jmx_path.exists():
            raise HTTPException(status_code=404, detail="JMX file not found on disk")

        # Create task record
        task = Task(
            name=f"Execute {file_record.original_name}",
            jmx_file_name=file_record.stored_name,
            jmx_file_path=file_record.file_path,
            jmx_file_hash=file_record.file_hash,
            status=TaskStatus.PENDING,
        )

        self.db.add(task)
        self.db.commit()

        # Start Celery task
        celery_task = execute_jmeter_task.delay(str(task.id), file_record.file_path)

        # Update task with Celery task ID
        task.process_id = celery_task.id
        self.db.commit()

        logger.info(f"JMeter execution task started: {task.id}")

        return {
            "task_id": str(task.id),
            "celery_task_id": celery_task.id,
            "status": "pending",
            "file_name": file_record.stored_name,
            "original_name": file_record.original_name,
            "message": "JMeter execution task started",
        }

    async def execute_jmx_sync_dev(self, file_name: str) -> dict:
        """Execute JMX file synchronously for development."""
        import subprocess

        # Find file record
        file_record = (
            self.db.query(FileRecord)
            .filter(FileRecord.stored_name == file_name, FileRecord.file_type == FileType.JMX, FileRecord.is_deleted is False)
            .first()
        )

        if not file_record:
            raise HTTPException(status_code=404, detail="JMX file not found")

        # Check if file exists on disk
        jmx_path = Path(file_record.file_path)
        if not jmx_path.exists():
            raise HTTPException(status_code=404, detail="JMX file not found on disk")

        # Create task record
        task = Task(
            name=f"Execute {file_record.original_name}",
            jmx_file_name=file_record.stored_name,
            jmx_file_path=file_record.file_path,
            jmx_file_hash=file_record.file_hash,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        self.db.add(task)
        self.db.commit()

        try:
            # Generate output file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{jmx_path.stem}_{timestamp}.jtl"
            output_path = settings.jtl_files_path / output_filename

            # Build JMeter command (simplified for development)
            if os.path.exists("/opt/homebrew/bin/jmeter") or os.path.exists("/usr/local/bin/jmeter"):
                jmeter_cmd = "jmeter"  # Use system JMeter if available
            else:
                logger.warning("JMeter not found in system PATH, using dummy execution")
                # Create dummy output for development
                with open(output_path, "w") as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write('<testResults version="1.2">\n')
                    f.write(
                        f'<httpSample t="100" lt="0" ts="{int(datetime.now().timestamp() * 1000)}" s="true" lb="Test" rc="200" rm="OK" tn="Thread Group 1-1" dt="text" by="1024"/>\n'
                    )
                    f.write("</testResults>\n")

                # Update task
                task.status = TaskStatus.COMPLETED
                task.jtl_file_name = output_filename
                task.jtl_file_path = str(output_path)
                task.cost_time = 0.1
                task.completed_at = datetime.utcnow()
                task.stdout = "Dummy execution for development"
                task.return_code = 0
                self.db.commit()

                logger.info(f"Dummy JMeter execution completed for development: {task.id}")

                return {
                    "task_id": str(task.id),
                    "status": "completed",
                    "file_name": file_record.stored_name,
                    "original_name": file_record.original_name,
                    "output_file": output_filename,
                    "created_at": task.created_at.isoformat(),
                    "message": "JMeter execution completed (development mode)",
                }

            # Real JMeter execution if available
            command = [jmeter_cmd, "-n", "-t", str(jmx_path), "-l", str(output_path)]

            logger.info(f"Executing JMeter command: {' '.join(command)}")

            start_time = datetime.utcnow()
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)  # 5 minutes timeout for development
            end_time = datetime.utcnow()

            cost_time = (end_time - start_time).total_seconds()

            # Update task with results
            task.stdout = result.stdout
            task.stderr = result.stderr
            task.return_code = result.returncode
            task.cost_time = cost_time
            task.completed_at = end_time

            if result.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.jtl_file_name = output_filename
                task.jtl_file_path = str(output_path)
                logger.info(f"JMeter execution completed successfully: {task.id}")
                message = "JMeter execution completed successfully"
                status = "completed"
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"JMeter execution failed: {result.stderr}")
                message = f"JMeter execution failed: {result.stderr}"
                status = "failed"

            self.db.commit()

            return {
                "task_id": str(task.id),
                "status": status,
                "file_name": file_record.stored_name,
                "original_name": file_record.original_name,
                "output_file": output_filename if status == "completed" else None,
                "cost_time": f"{cost_time:.2f}s",
                "created_at": task.created_at.isoformat(),
                "message": message,
            }

        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.stderr = "Execution timeout"
            task.completed_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"JMeter execution timeout: {task.id}")

            return {
                "task_id": str(task.id),
                "status": "failed",
                "file_name": file_record.stored_name,
                "original_name": file_record.original_name,
                "message": "JMeter execution timed out",
            }

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.stderr = str(e)
            task.completed_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"JMeter execution error: {e}")

            return {
                "task_id": str(task.id),
                "status": "failed",
                "file_name": file_record.stored_name,
                "original_name": file_record.original_name,
                "message": f"JMeter execution failed: {str(e)}",
            }

    def generate_html_report_async(self, jtl_file: str, task_id: Optional[str] = None) -> dict:
        """Generate HTML report asynchronously using Celery."""
        # Validate JTL file
        if not jtl_file.endswith(".jtl"):
            raise HTTPException(status_code=400, detail="Only JTL files are allowed")

        jtl_path = self.jtl_files_path / jtl_file
        if not jtl_path.exists():
            raise HTTPException(status_code=404, detail=f"JTL file not found: {jtl_file}")

        # Start Celery task for report generation
        celery_task = generate_html_report_task.delay(task_id or str(uuid.uuid4()), str(jtl_path))

        logger.info(f"HTML report generation task started for {jtl_file}")

        return {
            "celery_task_id": celery_task.id,
            "jtl_file": jtl_file,
            "status": "pending",
            "message": "HTML report generation started",
        }

    @staticmethod
    def generate_docker_compose(
        num_slaves: int,
        jmx_file: Path,
        docker_compose_file: Path,
        project_name: str,
        image: str = "justb4/jmeter",
        version: str = "5.5",
    ) -> Path:
        slaves = [f"jmeter-slave-{i}" for i in range(1, num_slaves + 1)]
        slave_list = ",".join(slaves)

        docker_compose_dict = {
            "version": "3.8",
            "services": {
                "jmeter-master": {
                    "image": f"{image}:{version}",
                    "command": f"-n -t /opt/apache-jmeter-{version}/test.jmx -R{slave_list} -Dserver.rmi.ssl.disable=true",
                    "volumes": [
                        "./plugins:/opt/apache-jmeter/plugins",
                        f"{jmx_file}:/opt/apache-jmeter-{version}/test.jmx",
                    ],
                    "depends_on": slaves,
                }
            },
        }

        for slave in slaves:
            docker_compose_dict["services"][slave] = {
                "image": f"{image}:{version}",
                "command": "-s -Dserver.rmi.ssl.disable=true",
                "environment": {"SLAVE_NAME": slave},
                "volumes": ["./plugins:/opt/apache-jmeter/plugins"],
            }
        docker_compose_dict["networks"] = {"default": {"name": f"jmeter-{project_name}"}}

        with open(docker_compose_file, "w") as f:
            yaml.dump(docker_compose_dict, f)

        return docker_compose_file

    @staticmethod
    def run_distributed_jmeter(docker_compose_file: str, project_name: str) -> RunCmdResp:
        logger.info(f"docker compose file: {docker_compose_file}")
        command = f"docker-compose -p {project_name} -f {docker_compose_file} up  -d"
        return JMeterManager.run_cmd(command)

    @staticmethod
    def stop_distributed_jmeter(docker_compose_file: str, project_name: str) -> RunCmdResp:
        command = f"docker-compose -p {project_name} -f {docker_compose_file} down"
        return JMeterManager.run_cmd(command)

    def get_task_status(self, task_id: str) -> dict:
        """Get task status from database."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": str(task.id),
            "name": task.name,
            "status": task.status.value,
            "jmx_file_name": task.jmx_file_name,
            "jtl_file_name": task.jtl_file_name,
            "cost_time": f"{task.cost_time:.2f}s" if task.cost_time else None,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.stderr if task.status == TaskStatus.FAILED else None,
        }

    def list_tasks(self, limit: int = 50, offset: int = 0) -> dict:
        """List tasks with pagination."""
        tasks = self.db.query(Task).order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
        total = self.db.query(Task).count()

        return {
            "tasks": [
                {
                    "task_id": str(task.id),
                    "name": task.name,
                    "status": task.status.value,
                    "jmx_file_name": task.jmx_file_name,
                    "jtl_file_name": task.jtl_file_name,
                    "cost_time": f"{task.cost_time:.2f}s" if task.cost_time else None,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in tasks
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def cancel_task(self, task_id: str) -> dict:
        """Cancel a running task."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise HTTPException(status_code=400, detail="Task cannot be cancelled")

        # Cancel Celery task if exists
        if task.process_id:
            from utils.celery_app import celery_app

            celery_app.control.revoke(task.process_id, terminate=True)

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Task cancelled: {task_id}")

        return {"task_id": task_id, "status": "cancelled", "message": "Task cancelled successfully"}


if __name__ == "__main__":
    # 示例用法
    jmeter_image = "justb4/jmeter"
    slave_count = 3
    rmi_port_start = 60000

    # remote_hosts = JMeterManager.create_jmeter_slaves(
    #     jmeter_image, slave_count, rmi_port_start
    # )
    parent_dir = Path.cwd().parent

    # 创建report目录的路径
    jmx_dir = parent_dir / "jmx_files"
    jtl_dir = parent_dir / "jtl_files"

    project_name: str = uuid.uuid4()

    docker_compose_file: Path = JMeterManager.generate_docker_compose(
        num_slaves=3,
        jmx_file=jmx_dir / "grafana-http-bin-json.jmx",
        docker_compose_file=parent_dir / "docker-compose.yml",
        project_name=project_name,
    )
    logger.info(f"docker compose file: {docker_compose_file}")

    JMeterManager.run_distributed_jmeter(
        docker_compose_file=str(docker_compose_file.absolute()),
        project_name=project_name,
    )
