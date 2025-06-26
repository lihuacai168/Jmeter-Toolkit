"""JMeter Toolkit main application."""
import os
import sys
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from database import get_db, Base, engine
from core.jmeter import JMeterManager
from middleware import error_handler_middleware, SecurityMiddleware
from models import APIResponse, HealthResponse, TaskResponse, FileUploadResponse
from utils import HealthChecker, get_prometheus_metrics


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
    logger.info("Starting JMeter Toolkit...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Create directories
    for directory in [settings.jmx_files_path, settings.jtl_files_path, settings.reports_path]:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Required directories created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down JMeter Toolkit...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A powerful toolkit for JMeter test management",
    lifespan=lifespan
)

# Add middleware
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
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


def get_jmeter_manager(db: Session = Depends(get_db)) -> JMeterManager:
    """Get JMeter manager instance."""
    return JMeterManager(db)


class FileTypeEnum(str, Enum):
    """File type enumeration for API."""
    jmx = "jmx"
    jtl = "jtl"


# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def frontend_home(request: Request):
    """Frontend home page."""
    return templates.TemplateResponse("index.html", {"request": request})


# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    health_status = HealthChecker.get_health_status()
    
    response_data = HealthResponse(
        status=health_status["status"],
        version=health_status["version"],
        timestamp=health_status["timestamp"],
        services=health_status["services"]
    )
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=response_data.dict(), status_code=status_code)


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return get_prometheus_metrics()


# File management endpoints
@app.post("/upload", response_model=APIResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Upload JMX file."""
    try:
        result = await jmeter_manager.upload_jmx(file)
        
        response_data = FileUploadResponse(
            file_name=result["file_name"],
            file_size=result["file_size"], 
            file_path=result["file_path"],
            upload_time=result.get("upload_time", "")
        )
        
        return APIResponse.success_response(
            data=response_data,
            message="File uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="UPLOAD_ERROR"
        )


@app.post("/execute", response_model=APIResponse[TaskResponse])
async def execute_jmx(
    file_name: str,
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Execute JMX file."""
    try:
        result = await jmeter_manager.execute_jmx_async(file_name)
        
        response_data = TaskResponse(
            task_id=result["task_id"],
            status=result["status"],
            file_name=result["file_name"],
            created_at=result.get("created_at", "")
        )
        
        return APIResponse.success_response(
            data=response_data,
            message="JMeter execution started"
        )
        
    except Exception as e:
        logger.error(f"JMeter execution error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="EXECUTION_ERROR"
        )


@app.post("/upload-and-execute", response_model=APIResponse[dict])
async def upload_and_execute(
    file: UploadFile = File(...),
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Upload JMX file and execute it."""
    try:
        # Upload file
        upload_result = await jmeter_manager.upload_jmx(file)
        
        # Execute file
        execution_result = await jmeter_manager.execute_jmx_async(upload_result["file_name"])
        
        return APIResponse.success_response(
            data={
                "upload": upload_result,
                "execution": execution_result
            },
            message="File uploaded and execution started"
        )
        
    except Exception as e:
        logger.error(f"Upload and execute error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="UPLOAD_EXECUTE_ERROR"
        )


@app.get("/tasks", response_model=APIResponse[dict])
async def list_tasks(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """List tasks with pagination."""
    try:
        result = jmeter_manager.list_tasks(limit=limit, offset=offset)
        
        return APIResponse.success_response(
            data=result,
            message="Tasks retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"List tasks error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="LIST_TASKS_ERROR"
        )


@app.get("/tasks/{task_id}", response_model=APIResponse[dict])
async def get_task_status(
    task_id: str,
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Get task status."""
    try:
        result = jmeter_manager.get_task_status(task_id)
        
        return APIResponse.success_response(
            data=result,
            message="Task status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get task status error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="TASK_STATUS_ERROR"
        )


@app.delete("/tasks/{task_id}", response_model=APIResponse[dict])
async def cancel_task(
    task_id: str,
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Cancel a task."""
    try:
        result = jmeter_manager.cancel_task(task_id)
        
        return APIResponse.success_response(
            data=result,
            message="Task cancelled successfully"
        )
        
    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="CANCEL_TASK_ERROR"
        )


@app.post("/reports", response_model=APIResponse[dict])
async def generate_report(
    jtl_file: str,
    task_id: Optional[str] = None,
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
):
    """Generate HTML report from JTL file."""
    try:
        result = jmeter_manager.generate_html_report_async(jtl_file, task_id)
        
        return APIResponse.success_response(
            data=result,
            message="Report generation started"
        )
        
    except Exception as e:
        logger.error(f"Generate report error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="REPORT_GENERATION_ERROR"
        )


@app.get("/files", response_model=APIResponse[dict])
async def list_files(
    file_type: FileTypeEnum,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List files by type."""
    try:
        if file_type == FileTypeEnum.jmx:
            directory = settings.jmx_files_path
            extension = ".jmx"
        else:
            directory = settings.jtl_files_path
            extension = ".jtl"
        
        files = []
        for file_path in directory.glob(f"*{extension}"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "path": str(file_path)
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        # Apply pagination
        total = len(files)
        paginated_files = files[offset:offset + limit]
        
        return APIResponse.success_response(
            data={
                "files": paginated_files,
                "total": total,
                "limit": limit,
                "offset": offset
            },
            message="Files retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        return APIResponse.error_response(
            message=str(e),
            code="LIST_FILES_ERROR"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )