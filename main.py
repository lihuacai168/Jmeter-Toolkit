"""JMeter Toolkit main application."""

import sys
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from database.base import Base

# Environment-aware database setup
if settings.environment == "development" or settings.database_url.startswith("sqlite"):
    # Development/SQLite configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    # Use simpler imports for development
    try:
        from core.jmeter import JMeterManager
        from middleware import SecurityMiddleware, error_handler_middleware
        from models import APIResponse, FileUploadResponse, HealthResponse, TaskResponse
        from utils import HealthChecker, get_prometheus_metrics

        PRODUCTION_MODE = True
    except ImportError:
        # Fallback for development without full dependencies
        PRODUCTION_MODE = False
        logger.warning("Running in simplified mode due to missing dependencies")
else:
    # Production configuration
    from core.jmeter import JMeterManager
    from database import engine
    from middleware import SecurityMiddleware, error_handler_middleware
    from models import APIResponse, FileUploadResponse, HealthResponse, TaskResponse
    from utils import HealthChecker, get_prometheus_metrics

    PRODUCTION_MODE = True

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)

if settings.log_file:
    logger.add(
        settings.log_file,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        level=settings.log_level,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting JMeter Toolkit in {settings.environment} mode...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create directories
    for directory in [settings.jmx_files_path, settings.jtl_files_path, settings.reports_path]:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Required directories created")

    if settings.environment == "development":
        logger.info("Development mode: Using simplified dependencies")

    yield

    # Shutdown
    logger.info("Shutting down JMeter Toolkit...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A powerful toolkit for JMeter test management",
    lifespan=lifespan,
)

# Add middleware conditionally
if PRODUCTION_MODE:
    app.middleware("http")(error_handler_middleware)
    app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/reports", StaticFiles(directory=str(settings.reports_path), html=True), name="reports")
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
if Path("templates").exists():
    templates = Jinja2Templates(directory="templates")


def get_jmeter_manager(db: Session = Depends(get_db)) -> Optional[JMeterManager]:
    """Get JMeter manager instance."""
    if PRODUCTION_MODE:
        return JMeterManager(db)
    return None


class FileTypeEnum(str, Enum):
    """File type enumeration for API."""

    jmx = "jmx"
    jtl = "jtl"


# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def frontend_home(request: Request):
    """Frontend home page."""
    if "templates" in locals():
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<h1>JMeter Toolkit</h1><p>API available at <a href='/docs'>/docs</a></p>")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime

    # Use simplified health check for development and testing environments
    if not PRODUCTION_MODE or settings.environment in ["development", "testing"]:
        return {
            "success": True,
            "data": {"status": "healthy", "version": settings.app_version, "environment": settings.environment},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Full health check for production
    health_status = HealthChecker.get_health_status()

    # Convert complex service status to simple strings
    services_status = {}
    for service_name, service_data in health_status["services"].items():
        services_status[service_name] = service_data["status"]

    response_data = HealthResponse(
        status=health_status["status"],
        version=health_status["version"],
        timestamp=health_status["timestamp"],
        services=services_status,
    )

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=response_data.dict(), status_code=status_code)


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    if PRODUCTION_MODE:
        return get_prometheus_metrics()
    else:
        return "# Metrics not available in development mode"


# File management endpoints
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)):
    """Upload JMX file."""
    try:
        if PRODUCTION_MODE and jmeter_manager:
            result = await jmeter_manager.upload_jmx(file)

            response_data = FileUploadResponse(
                file_name=result["file_name"],
                file_size=result["file_size"],
                file_path=result["file_path"],
                upload_time=result.get("upload_time", ""),
            )

            return APIResponse.success_response(data=response_data, message="File uploaded successfully")
        else:
            # Simplified upload for development
            if not file.filename.endswith(".jmx"):
                raise HTTPException(status_code=400, detail="Only JMX files allowed")

            import shutil
            from datetime import datetime

            # Generate safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{Path(file.filename).stem}_{timestamp}.jmx"
            file_path = settings.jmx_files_path / safe_filename

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            return {
                "success": True,
                "data": {
                    "file_name": safe_filename,
                    "file_size": file_path.stat().st_size,
                    "file_path": str(file_path),
                    "upload_time": datetime.utcnow().isoformat(),
                },
                "message": "File uploaded successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="UPLOAD_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_jmx(request: dict, jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)):
    """Execute JMX file."""
    try:
        file_name = request.get("file_name")
        if not file_name:
            raise HTTPException(status_code=400, detail="file_name is required")

        if PRODUCTION_MODE and jmeter_manager:
            result = await jmeter_manager.execute_jmx_async(file_name)

            response_data = TaskResponse(
                task_id=result["task_id"],
                status=result["status"],
                file_name=result["file_name"],
                created_at=result.get("created_at", ""),
            )

            return APIResponse.success_response(data=response_data, message="JMeter execution started")
        else:
            # Simplified execution for development
            import uuid
            from datetime import datetime

            # Check if file exists
            jmx_path = settings.jmx_files_path / file_name
            logger.info(f"Looking for JMX file at: {jmx_path}")
            logger.info(f"File exists: {jmx_path.exists()}")

            if not jmx_path.exists():
                # List available files for debugging
                available_files = list(settings.jmx_files_path.glob("*.jmx"))
                logger.error(f"Available JMX files: {[f.name for f in available_files]}")
                raise HTTPException(status_code=404, detail=f"JMX file not found: {file_name}")

            # Create mock task
            task_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{jmx_path.stem}_{timestamp}.jtl"
            output_path = settings.jtl_files_path / output_filename

            # Create mock JTL file
            with open(output_path, "w") as f:
                f.write(
                    """<?xml version="1.0" encoding="UTF-8"?>
<testResults version="1.2">
<httpSample t="150" lt="0" ts="{}" s="true" lb="HTTP Request" rc="200" rm="OK" tn="Thread Group 1-1" dt="text" by="1024"/>
<httpSample t="200" lt="0" ts="{}" s="true" lb="HTTP Request" rc="200" rm="OK" tn="Thread Group 1-2" dt="text" by="2048"/>
</testResults>""".format(
                        int(datetime.now().timestamp() * 1000), int(datetime.now().timestamp() * 1000) + 1000
                    )
                )

            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "status": "completed",
                    "file_name": file_name,
                    "output_file": output_filename,
                    "cost_time": "0.15s",
                    "created_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                },
                "message": "JMeter execution completed (simulated)",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JMeter execution error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="EXECUTION_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-and-execute")
async def upload_and_execute(
    file: UploadFile = File(...), jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)
):
    """Upload JMX file and execute it."""
    try:
        # Upload file
        upload_result = await upload_file(file, jmeter_manager)

        # Extract upload data based on response type
        if hasattr(upload_result, "data"):  # APIResponse object
            upload_data = upload_result.data.__dict__ if hasattr(upload_result.data, "__dict__") else upload_result.data
        elif isinstance(upload_result, dict) and "data" in upload_result:  # Dict response
            upload_data = upload_result["data"]
        else:
            raise ValueError("Invalid upload response format")

        # Execute file
        file_name = upload_data.get("file_name") if isinstance(upload_data, dict) else upload_data.file_name
        execution_result = await execute_jmx({"file_name": file_name}, jmeter_manager)

        # Extract execution data based on response type
        if hasattr(execution_result, "data"):  # APIResponse object
            execution_data = (
                execution_result.data.__dict__ if hasattr(execution_result.data, "__dict__") else execution_result.data
            )
        elif isinstance(execution_result, dict) and "data" in execution_result:  # Dict response
            execution_data = execution_result["data"]
        else:
            raise ValueError("Invalid execution response format")

        if PRODUCTION_MODE:
            return APIResponse.success_response(
                data={"upload": upload_data, "execution": execution_data}, message="File uploaded and execution started"
            )
        else:
            from datetime import datetime

            return {
                "success": True,
                "data": {"upload": upload_data, "execution": execution_data},
                "message": "File uploaded and executed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Upload and execute error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="UPLOAD_EXECUTE_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def list_tasks(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager),
):
    """List tasks with pagination."""
    try:
        if PRODUCTION_MODE and jmeter_manager:
            result = jmeter_manager.list_tasks(limit=limit, offset=offset)

            return APIResponse.success_response(data=result, message="Tasks retrieved successfully")
        else:
            # Simplified task listing for development
            from datetime import datetime

            return {
                "success": True,
                "data": {"tasks": [], "total": 0},
                "message": "Tasks retrieved successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"List tasks error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="LIST_TASKS_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str, jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)):
    """Get task status."""
    try:
        if PRODUCTION_MODE and jmeter_manager:
            result = jmeter_manager.get_task_status(task_id)

            return APIResponse.success_response(data=result, message="Task status retrieved successfully")
        else:
            # Simplified task status for development
            raise HTTPException(status_code=404, detail="Task not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task status error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="TASK_STATUS_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def list_files(
    file_type: FileTypeEnum,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search term for fuzzy filename matching"),
):
    """List files by type."""
    try:
        if file_type == FileTypeEnum.jmx:
            directory = settings.jmx_files_path
            extension = ".jmx"
        elif file_type == FileTypeEnum.jtl:
            directory = settings.jtl_files_path
            extension = ".jtl"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        files = []
        for file_path in directory.glob(f"*{extension}"):
            if file_path.is_file():
                # Apply search filter if search term is provided
                if search and search.strip():
                    search_term = search.strip().lower()
                    filename_lower = file_path.name.lower()
                    # Fuzzy search: check if search term is contained in filename
                    if search_term not in filename_lower:
                        continue

                stat = file_path.stat()
                files.append({"name": file_path.name, "size": stat.st_size, "modified": stat.st_mtime, "path": str(file_path)})

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

        # Apply pagination
        total = len(files)
        paginated_files = files[offset : offset + limit]

        if PRODUCTION_MODE:
            return APIResponse.success_response(
                data={"files": paginated_files, "total": total, "limit": limit, "offset": offset},
                message="Files retrieved successfully",
            )
        else:
            from datetime import datetime

            return {
                "success": True,
                "data": {"files": paginated_files, "total": total},
                "message": "Files retrieved successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List files error: {e}")
        if PRODUCTION_MODE:
            return APIResponse.error_response(message=str(e), code="LIST_FILES_ERROR")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_type}/{file_name}")
async def download_file(file_type: str, file_name: str):
    """Download file."""
    try:
        if file_type == "jmx":
            directory = settings.jmx_files_path
        elif file_type == "jtl":
            directory = settings.jtl_files_path
        elif file_type == "report":
            directory = settings.reports_path
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        file_path = directory / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        from fastapi.responses import FileResponse

        return FileResponse(path=str(file_path), filename=file_name, media_type="application/octet-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report/{task_id}")
async def generate_html_report(task_id: str, jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)):
    """Generate HTML report from JTL file."""
    try:
        import subprocess

        if PRODUCTION_MODE and jmeter_manager:
            # Get task info from database
            task_data = jmeter_manager.get_task_status(task_id)
            if not task_data.get("jtl_file_name"):
                raise HTTPException(status_code=404, detail="Task has no JTL file")

            jtl_file_name = task_data["jtl_file_name"]
            jtl_path = settings.jtl_files_path / jtl_file_name

        else:
            # Development mode - find JTL file
            jtl_files = list(settings.jtl_files_path.glob("*.jtl"))
            if not jtl_files:
                raise HTTPException(status_code=404, detail="No JTL files found")
            jtl_path = jtl_files[0]  # Use first available JTL file for demo

        if not jtl_path.exists():
            raise HTTPException(status_code=404, detail="JTL file not found")

        # Create report directory
        report_dir_name = jtl_path.stem
        report_dir = settings.reports_path / report_dir_name

        # Remove existing report directory if exists
        if report_dir.exists():
            import shutil

            shutil.rmtree(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        # Check if JMeter is available
        import os
        import shutil

        jmeter_available = (
            os.path.exists("/opt/homebrew/bin/jmeter")
            or os.path.exists("/usr/local/bin/jmeter")
            or shutil.which("jmeter") is not None
        )

        if jmeter_available:
            # Use real JMeter to generate HTML report
            command = ["jmeter", "-g", str(jtl_path), "-o", str(report_dir)]
            logger.info(f"Generating HTML report with command: {' '.join(command)}")

            result = subprocess.run(command, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(f"HTML report generated successfully: {report_dir}")
                return APIResponse.success_response(
                    data={
                        "task_id": task_id,
                        "report_path": f"/reports/{report_dir_name}/",
                        "message": "HTML report generated successfully",
                    },
                    message="HTML report generated successfully",
                )
            else:
                logger.error(f"JMeter report generation failed: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"Report generation failed: {result.stderr}")
        else:
            # Create mock report for development
            logger.warning("JMeter not found, creating mock HTML report")
            (report_dir / "index.html").write_text(
                f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>JMeter Test Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                    .summary {{ margin: 20px 0; }}
                    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                    .metric {{ background: white; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>JMeter Test Report</h1>
                    <p>Generated from: {jtl_path.name}</p>
                    <p>Report ID: {task_id}</p>
                </div>

                <div class="summary">
                    <h2>Test Summary</h2>
                    <div class="metrics">
                        <div class="metric">
                            <h3>Total Samples</h3>
                            <p>100</p>
                        </div>
                        <div class="metric">
                            <h3>Success Rate</h3>
                            <p>95%</p>
                        </div>
                        <div class="metric">
                            <h3>Average Response Time</h3>
                            <p>150ms</p>
                        </div>
                        <div class="metric">
                            <h3>Max Response Time</h3>
                            <p>500ms</p>
                        </div>
                    </div>
                </div>

                <div>
                    <h2>Note</h2>
                    <p>This is a mock report for development purposes. Install JMeter to generate real reports.</p>
                </div>
            </body>
            </html>
            """
            )

            # Create additional mock files
            (report_dir / "content").mkdir(exist_ok=True)
            (report_dir / "content" / "styles.css").write_text("/* Mock CSS */")
            (report_dir / "content" / "report.json").write_text('{"summary": "Mock report data"}')

            return APIResponse.success_response(
                data={
                    "task_id": task_id,
                    "report_path": f"/reports/{report_dir_name}/",
                    "message": "Mock HTML report generated (JMeter not found)",
                },
                message="Mock HTML report generated",
            )

    except subprocess.TimeoutExpired:
        logger.error("HTML report generation timeout")
        raise HTTPException(status_code=500, detail="Report generation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate HTML report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-report-zip/{task_id}")
async def download_html_report_zip(task_id: str, jmeter_manager: Optional[JMeterManager] = Depends(get_jmeter_manager)):
    """Download HTML report as ZIP file."""
    try:
        import tempfile
        import zipfile
        from pathlib import Path

        # 使用通用的方法查找报告目录
        if PRODUCTION_MODE and jmeter_manager:
            # Production mode - get task info from database
            task_data = jmeter_manager.get_task_status(task_id)
            report_path = task_data.get("report_path")
        else:
            # Development mode - check if this is using dev_server data
            try:
                # Try to load from dev_server data files if available
                import json

                tasks_file = Path("dev_tasks.json")
                if tasks_file.exists():
                    with open(tasks_file, "r", encoding="utf-8") as f:
                        tasks_db = json.load(f)
                    if task_id not in tasks_db:
                        raise HTTPException(status_code=404, detail="Task not found")
                    task = tasks_db[task_id]
                    report_path = task.get("report_path")
                else:
                    raise HTTPException(status_code=404, detail="No task data available")
            except Exception as e:
                logger.error(f"Error loading dev task data: {e}")
                raise HTTPException(status_code=500, detail="Error accessing task data")

        if not report_path:
            raise HTTPException(status_code=404, detail="No report available for this task")

        # 从report_path提取目录名称 (去掉前缀/reports/和后缀/)
        if report_path.startswith("/reports/"):
            report_dir_name = report_path[9:]  # 去掉 "/reports/"
            if report_dir_name.endswith("/"):
                report_dir_name = report_dir_name[:-1]  # 去掉末尾的 "/"
        else:
            raise HTTPException(status_code=404, detail="Invalid report path")

        report_dir = settings.reports_path / report_dir_name

        if not report_dir.exists():
            raise HTTPException(status_code=404, detail="HTML report not found")

        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            zip_path = tmp_file.name

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add all files in report directory to ZIP
                for file_path in report_dir.rglob("*"):
                    if file_path.is_file():
                        # Calculate relative path within ZIP
                        relative_path = file_path.relative_to(report_dir)
                        zip_file.write(file_path, relative_path)

            # Return ZIP file as download
            from fastapi.responses import FileResponse

            zip_filename = f"jmeter_report_{report_dir_name}.zip"

            # Clean up temp file after response
            def cleanup():
                try:
                    Path(zip_path).unlink()
                except Exception:
                    pass

            response = FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

            # Schedule cleanup (FastAPI will handle this after response is sent)
            import threading

            timer = threading.Timer(10.0, cleanup)  # Clean up after 10 seconds
            timer.start()

            return response

        except Exception as e:
            # Clean up on error
            try:
                Path(zip_path).unlink()
            except Exception:
                pass
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download HTML report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 Server: http://{settings.host}:{settings.port}")
    print(f"📖 API Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🔧 Environment: {settings.environment}")
    print(f"💾 Database: {settings.database_url}")
    print("⏹️  Press Ctrl+C to stop")

    uvicorn.run(
        "main:app", host=settings.host, port=settings.port, reload=settings.reload, log_level=settings.log_level.lower()
    )
