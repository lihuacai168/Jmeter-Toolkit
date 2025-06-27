"""Celery tasks."""

import os
import shutil
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from celery import current_task
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal, Task, TaskStatus
from utils.celery_app import celery_app
from utils.security import CommandSanitizer


@celery_app.task(bind=True)
def execute_jmeter_task(self, task_id: str, jmx_file_path: str) -> Dict[str, Any]:
    """Execute JMeter test task."""
    db: Session = SessionLocal()

    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.process_id = current_task.request.id
        db.commit()

        logger.info(f"Starting JMeter execution for task {task_id}")

        # Prepare output file path
        jmx_path = Path(jmx_file_path)
        if not jmx_path.exists():
            raise FileNotFoundError(f"JMX file not found: {jmx_file_path}")

        # Generate output file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{jmx_path.stem}_{timestamp}.jtl"
        output_path = settings.jtl_files_path / output_filename

        # Build safe JMeter command
        jmeter_cmd = f"{settings.jmeter_home}/bin/jmeter"
        command_args = [
            "-n",  # non-GUI mode
            "-t",
            str(jmx_path),  # test plan
            "-l",
            str(output_path),  # log file
            "-j",
            str(settings.jtl_files_path / f"{jmx_path.stem}_{timestamp}.log"),  # jmeter log
            "-Jjmeter.save.saveservice.output_format=xml",
            "-Jjmeter.save.saveservice.response_data.on_error=true",
        ]

        # Build safe command
        safe_command = CommandSanitizer.build_safe_command(jmeter_cmd, command_args)
        command_str = " ".join(safe_command)

        # Update task with command
        task.command = command_str
        task.jtl_file_name = output_filename
        task.jtl_file_path = str(output_path)
        db.commit()

        logger.info(f"Executing command: {command_str}")

        # Execute command
        start_time = datetime.utcnow()
        process = subprocess.Popen(
            safe_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # Create new process group
        )

        # Wait for completion
        stdout, stderr = process.communicate(timeout=settings.jmeter_timeout)
        end_time = datetime.utcnow()

        # Calculate execution time
        cost_time = (end_time - start_time).total_seconds()

        # Update task with results
        task.stdout = stdout
        task.stderr = stderr
        task.return_code = process.returncode
        task.cost_time = cost_time
        task.completed_at = end_time

        if process.returncode == 0:
            task.status = TaskStatus.COMPLETED
            logger.info(f"JMeter execution completed successfully for task {task_id}")
            result = {
                "status": "success",
                "task_id": task_id,
                "output_file": output_filename,
                "cost_time": f"{cost_time:.2f}s",
                "message": "JMeter execution completed successfully",
            }
        else:
            task.status = TaskStatus.FAILED
            logger.error(f"JMeter execution failed for task {task_id}: {stderr}")
            result = {
                "status": "failed",
                "task_id": task_id,
                "error": stderr,
                "cost_time": f"{cost_time:.2f}s",
                "message": f"JMeter execution failed with return code {process.returncode}",
            }

        db.commit()
        return result

    except subprocess.TimeoutExpired:
        logger.error(f"JMeter execution timeout for task {task_id}")
        task.status = TaskStatus.FAILED
        task.stderr = "Execution timeout"
        task.completed_at = datetime.utcnow()
        db.commit()

        return {"status": "failed", "task_id": task_id, "error": "Execution timeout", "message": "JMeter execution timed out"}

    except Exception as exc:
        logger.error(f"JMeter execution error for task {task_id}: {traceback.format_exc()}")
        task.status = TaskStatus.FAILED
        task.stderr = str(exc)
        task.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(exc),
            "message": "JMeter execution failed due to internal error",
        }

    finally:
        db.close()


@celery_app.task(bind=True)
def generate_html_report_task(self, task_id: str, jtl_file_path: str) -> Dict[str, Any]:
    """Generate HTML report from JTL file."""
    db: Session = SessionLocal()

    try:
        logger.info(f"Generating HTML report for task {task_id}")

        # Validate JTL file
        jtl_path = Path(jtl_file_path)
        if not jtl_path.exists():
            raise FileNotFoundError(f"JTL file not found: {jtl_file_path}")

        # Prepare report directory
        report_dir = settings.reports_path / jtl_path.stem
        if report_dir.exists():
            logger.info(f"Removing existing report directory: {report_dir}")
            shutil.rmtree(report_dir)

        # Build JMeter report generation command
        jmeter_cmd = f"{settings.jmeter_home}/bin/jmeter"
        command_args = ["-g", str(jtl_path), "-o", str(report_dir)]  # input JTL file  # output report directory

        # Build safe command
        safe_command = CommandSanitizer.build_safe_command(jmeter_cmd, command_args)
        command_str = " ".join(safe_command)

        logger.info(f"Executing report command: {command_str}")

        # Execute command
        start_time = datetime.utcnow()
        process = subprocess.Popen(safe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
        end_time = datetime.utcnow()

        generation_time = (end_time - start_time).total_seconds()

        if process.returncode == 0:
            logger.info(f"HTML report generated successfully for task {task_id}")
            return {
                "status": "success",
                "task_id": task_id,
                "report_path": str(report_dir),
                "generation_time": f"{generation_time:.2f}s",
                "message": "HTML report generated successfully",
            }
        else:
            logger.error(f"HTML report generation failed for task {task_id}: {stderr}")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": stderr,
                "message": f"HTML report generation failed with return code {process.returncode}",
            }

    except Exception as exc:
        logger.error(f"HTML report generation error for task {task_id}: {traceback.format_exc()}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(exc),
            "message": "HTML report generation failed due to internal error",
        }

    finally:
        db.close()


@celery_app.task
def cleanup_old_files(days: int = 7) -> Dict[str, Any]:
    """Clean up old files and reports."""
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logger.info(f"Cleaning up files older than {cutoff_date}")

        cleaned_files = 0

        # Clean up JTL files
        for jtl_file in settings.jtl_files_path.glob("*.jtl"):
            if datetime.fromtimestamp(jtl_file.stat().st_mtime) < cutoff_date:
                jtl_file.unlink()
                cleaned_files += 1
                logger.info(f"Deleted old JTL file: {jtl_file}")

        # Clean up report directories
        for report_dir in settings.reports_path.iterdir():
            if report_dir.is_dir() and datetime.fromtimestamp(report_dir.stat().st_mtime) < cutoff_date:
                shutil.rmtree(report_dir)
                cleaned_files += 1
                logger.info(f"Deleted old report directory: {report_dir}")

        return {"status": "success", "cleaned_files": cleaned_files, "message": f"Cleaned up {cleaned_files} old files"}

    except Exception as exc:
        logger.error(f"File cleanup error: {traceback.format_exc()}")
        return {"status": "failed", "error": str(exc), "message": "File cleanup failed"}
