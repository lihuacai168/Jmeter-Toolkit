#!/usr/bin/env python3
"""简化的开发服务器，使用内存数据库和基本功能。"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 强制设置环境变量
os.environ["DATABASE_URL"] = "sqlite:///./dev_jmeter_toolkit.db"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "INFO"

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel
from typing import Optional
import shutil
import uuid
from datetime import datetime
import json

# 创建目录
for directory in ["jmx_files", "jtl_files", "reports", "static", "templates"]:
    Path(directory).mkdir(exist_ok=True)

# 内存数据存储
tasks_db = {}
files_db = {}

# FastAPI 应用
app = FastAPI(title="JMeter Toolkit", version="2.0.0-dev", description="JMeter Toolkit Development Server")

# 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/reports", StaticFiles(directory="reports", html=True), name="reports")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板
templates = Jinja2Templates(directory="templates")


# 响应模型
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: str


@app.get("/", response_class=HTMLResponse)
async def home(request):
    """主页."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查."""
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={"status": "healthy", "version": "2.0.0-dev", "environment": "development"},
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传JMX文件."""
    try:
        if not file.filename.endswith(".jmx"):
            raise HTTPException(status_code=400, detail="Only JMX files allowed")

        # 生成安全文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{Path(file.filename).stem}_{timestamp}.jmx"
        file_path = Path("jmx_files") / safe_filename

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 记录文件信息
        file_id = str(uuid.uuid4())
        files_db[file_id] = {
            "id": file_id,
            "original_name": file.filename,
            "stored_name": safe_filename,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        return APIResponse(
            success=True,
            message="File uploaded successfully",
            data={
                "file_name": safe_filename,
                "file_size": file_path.stat().st_size,
                "file_path": str(file_path),
                "upload_time": datetime.utcnow().isoformat(),
            },
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return APIResponse(success=False, message=str(e), timestamp=datetime.utcnow().isoformat())


class ExecuteRequest(BaseModel):
    file_name: str


@app.post("/execute")
async def execute_jmx(request: ExecuteRequest):
    """执行JMX文件（开发模式模拟）."""
    try:
        # 检查文件是否存在
        jmx_path = Path("jmx_files") / request.file_name
        if not jmx_path.exists():
            raise HTTPException(status_code=404, detail="JMX file not found")

        # 创建任务
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{jmx_path.stem}_{timestamp}.jtl"
        output_path = Path("jtl_files") / output_filename

        # 模拟JMeter执行，创建虚拟JTL文件
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

        # 记录任务
        tasks_db[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "file_name": request.file_name,
            "output_file": output_filename,
            "cost_time": "0.15s",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

        return APIResponse(
            success=True,
            message="JMeter execution completed (simulated)",
            data=tasks_db[task_id],
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return APIResponse(success=False, message=str(e), timestamp=datetime.utcnow().isoformat())


@app.post("/upload-and-execute")
async def upload_and_execute(file: UploadFile = File(...)):
    """上传并执行JMX文件."""
    try:
        # 上传文件
        upload_result = await upload_file(file)
        if not upload_result.success:
            return upload_result

        # 执行文件
        file_name = upload_result.data["file_name"]
        execute_request = ExecuteRequest(file_name=file_name)
        execute_result = await execute_jmx(execute_request)

        return APIResponse(
            success=True,
            message="File uploaded and executed successfully",
            data={"upload": upload_result.data, "execution": execute_result.data},
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and execute error: {e}")
        return APIResponse(success=False, message=str(e), timestamp=datetime.utcnow().isoformat())


@app.get("/tasks")
async def list_tasks():
    """列出所有任务."""
    tasks = list(tasks_db.values())
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    return APIResponse(
        success=True,
        message="Tasks retrieved successfully",
        data={"tasks": tasks, "total": len(tasks)},
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(
        success=True,
        message="Task status retrieved successfully",
        data=tasks_db[task_id],
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/files")
async def list_files(file_type: str = "jmx"):
    """列出文件."""
    try:
        if file_type == "jmx":
            directory = Path("jmx_files")
            extension = ".jmx"
        elif file_type == "jtl":
            directory = Path("jtl_files")
            extension = ".jtl"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        files = []
        for file_path in directory.glob(f"*{extension}"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({"name": file_path.name, "size": stat.st_size, "modified": stat.st_mtime, "path": str(file_path)})

        files.sort(key=lambda x: x["modified"], reverse=True)

        return APIResponse(
            success=True,
            message="Files retrieved successfully",
            data={"files": files, "total": len(files)},
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List files error: {e}")
        return APIResponse(success=False, message=str(e), timestamp=datetime.utcnow().isoformat())


@app.get("/download/{file_type}/{file_name}")
async def download_file(file_type: str, file_name: str):
    """下载文件."""
    try:
        if file_type == "jmx":
            directory = Path("jmx_files")
        elif file_type == "jtl":
            directory = Path("jtl_files")
        elif file_type == "report":
            directory = Path("reports")
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        file_path = directory / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(path=str(file_path), filename=file_name, media_type="application/octet-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 JMeter Toolkit 开发服务器")
    print("📍 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("⏹️  按 Ctrl+C 停止服务器")

    uvicorn.run("simple_dev:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
