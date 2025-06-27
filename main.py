"""JMeter Toolkit main application."""

import os
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
from database.models import AuditLog, FileRecord, FileType, Report, Task, TaskStatus

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
    if PRODUCTION_MODE:
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
    else:
        # Simplified health check for development
        from datetime import datetime

        return {
            "success": True,
            "data": {"status": "healthy", "version": settings.app_version, "environment": settings.environment},
            "timestamp": datetime.utcnow().isoformat(),
        }


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
            import uuid
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
            if not jmx_path.exists():
                raise HTTPException(status_code=404, detail="JMX file not found")

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
        if hasattr(upload_result, "success"):
            upload_data = upload_result.data
        else:
            upload_data = upload_result["data"]

        # Execute file
        execution_result = await execute_jmx({"file_name": upload_data["file_name"]}, jmeter_manager)
        if hasattr(execution_result, "data"):
            execution_data = execution_result.data
        else:
            execution_data = execution_result["data"]

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
async def list_files(file_type: FileTypeEnum, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
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
