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
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "INFO"

import asyncio
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

# 创建目录
for directory in ["jmx_files", "jtl_files", "reports", "static", "templates"]:
    Path(directory).mkdir(exist_ok=True)

# 数据持久化存储
TASKS_DB_FILE = Path("dev_tasks.json")
FILES_DB_FILE = Path("dev_files.json")


def load_data():
    """加载持久化数据"""
    tasks_db = {}
    files_db = {}

    try:
        if TASKS_DB_FILE.exists():
            with open(TASKS_DB_FILE, "r", encoding="utf-8") as f:
                tasks_db = json.load(f)
                logger.info(f"Loaded {len(tasks_db)} tasks from {TASKS_DB_FILE}")
    except Exception as e:
        logger.warning(f"Failed to load tasks data: {e}")

    try:
        if FILES_DB_FILE.exists():
            with open(FILES_DB_FILE, "r", encoding="utf-8") as f:
                files_db = json.load(f)
                logger.info(f"Loaded {len(files_db)} files from {FILES_DB_FILE}")
    except Exception as e:
        logger.warning(f"Failed to load files data: {e}")

    return tasks_db, files_db


def save_tasks_data(tasks_db):
    """保存任务数据"""
    try:
        with open(TASKS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save tasks data: {e}")


def save_files_data(files_db):
    """保存文件数据"""
    try:
        with open(FILES_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(files_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save files data: {e}")


# 加载数据
tasks_db, files_db = load_data()

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
        save_files_data(files_db)

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


async def auto_generate_report(task_id: str):
    """自动生成HTML报告 (用于JMeter执行完成后)."""
    try:
        import shutil

        # Find task info
        if task_id not in tasks_db:
            logger.error(f"Auto report: Task {task_id} not found")
            return

        task = tasks_db[task_id]
        if task["status"] != "completed":
            logger.error(f"Auto report: Task {task_id} not completed")
            return

        # Find corresponding JTL file
        output_file = task.get("output_file")
        if not output_file:
            logger.error(f"Auto report: No JTL file found for task {task_id}")
            return

        jtl_path = Path("jtl_files") / output_file
        if not jtl_path.exists():
            logger.error(f"Auto report: JTL file not found: {jtl_path}")
            return

        # Create report directory
        report_dir_name = jtl_path.stem
        report_dir = Path("reports") / report_dir_name

        # Remove existing report directory if exists
        if report_dir.exists():
            shutil.rmtree(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        # Check if JMeter is available
        jmeter_available = (
            os.path.exists("/opt/homebrew/bin/jmeter")
            or os.path.exists("/usr/local/bin/jmeter")
            or shutil.which("jmeter") is not None
        )

        if jmeter_available:
            # Use real JMeter to generate HTML report with async subprocess
            command = ["jmeter", "-g", str(jtl_path), "-o", str(report_dir)]
            logger.info(f"Auto report: Generating HTML report with command: {' '.join(command)}")

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode == 0:
                logger.info(f"Auto report: HTML report generated successfully: {report_dir}")
                # Update task with report path
                tasks_db[task_id]["report_path"] = f"/reports/{report_dir_name}/"
                save_tasks_data(tasks_db)
            else:
                logger.error(f"Auto report: JMeter report generation failed: {stderr.decode()}")
        else:
            # Create mock report for development
            logger.warning("Auto report: JMeter not found, creating mock HTML report")
            (report_dir / "index.html").write_text(
                f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>JMeter Test Report - {task_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .mock {{ background: #fffacd; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>JMeter Test Report (Mock)</h1>
                <div class="mock">
                    <p>This is a mock report generated automatically for development purposes.</p>
                    <p>Task ID: {task_id}</p>
                    <p>Generated: {datetime.now().isoformat()}</p>
                    <p>Install JMeter to generate real reports.</p>
                </div>
            </body>
            </html>
            """
            )
            # Update task with report path
            tasks_db[task_id]["report_path"] = f"/reports/{report_dir_name}/"
            save_tasks_data(tasks_db)
            logger.info(f"Auto report: Mock HTML report generated: {report_dir}")

    except Exception as e:
        logger.error(f"Auto report: Error generating report for task {task_id}: {e}")


async def execute_jmeter_background(task_id: str, command: list, output_path: Path):
    """在后台执行JMeter命令."""
    try:
        logger.info(f"Background task {task_id}: Starting JMeter execution")

        # 更新任务状态为运行中
        if task_id in tasks_db:
            tasks_db[task_id]["status"] = "running"
            save_tasks_data(tasks_db)

        start_time = datetime.now()

        # 使用异步subprocess执行命令
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        end_time = datetime.now()
        cost_time = (end_time - start_time).total_seconds()

        # 更新任务状态
        if task_id in tasks_db:
            if process.returncode == 0:
                tasks_db[task_id]["status"] = "completed"
                tasks_db[task_id]["message"] = "JMeter execution completed successfully"
                logger.info(f"Background task {task_id}: JMeter execution completed successfully")

                # 自动生成HTML报告
                try:
                    logger.info(f"Background task {task_id}: Starting automatic HTML report generation")
                    # 调用生成报告的函数
                    await auto_generate_report(task_id)
                    logger.info(f"Background task {task_id}: HTML report generated automatically")
                except Exception as e:
                    logger.warning(f"Background task {task_id}: Failed to auto-generate HTML report: {e}")
                    # 报告生成失败不影响任务完成状态
            else:
                tasks_db[task_id]["status"] = "failed"
                tasks_db[task_id]["message"] = f"JMeter execution failed: {stderr.decode()}"
                logger.error(f"Background task {task_id}: JMeter execution failed: {stderr.decode()}")

            tasks_db[task_id]["cost_time"] = f"{cost_time:.2f}s"
            tasks_db[task_id]["completed_at"] = end_time.isoformat()
            save_tasks_data(tasks_db)

    except asyncio.TimeoutError:
        logger.error(f"Background task {task_id}: JMeter execution timed out")
        if task_id in tasks_db:
            tasks_db[task_id]["status"] = "failed"
            tasks_db[task_id]["message"] = "JMeter execution timed out (5 minutes)"
            save_tasks_data(tasks_db)
    except Exception as e:
        logger.error(f"Background task {task_id}: JMeter execution error: {e}")
        if task_id in tasks_db:
            tasks_db[task_id]["status"] = "failed"
            tasks_db[task_id]["message"] = f"JMeter execution error: {str(e)}"
            save_tasks_data(tasks_db)


@app.post("/execute")
async def execute_jmx(request: ExecuteRequest):
    """执行JMX文件."""
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

        # 检查是否有真实的JMeter可用
        jmeter_available = False
        jmeter_path = shutil.which("jmeter")
        if jmeter_path:
            jmeter_available = True
            logger.info(f"JMeter found at: {jmeter_path}")
        else:
            # 检查常见安装路径
            for path in ["/opt/homebrew/bin/jmeter", "/usr/local/bin/jmeter"]:
                if os.path.exists(path):
                    jmeter_available = True
                    logger.info(f"JMeter found at: {path}")
                    break

        logger.info(f"JMeter availability check: {jmeter_available}")

        # 创建任务记录，立即返回，在后台执行
        task = {
            "task_id": task_id,
            "status": "pending",
            "file_name": request.file_name,
            "output_file": output_filename,
            "cost_time": "0s",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }

        # 保存任务到内存
        tasks_db[task_id] = task
        save_tasks_data(tasks_db)

        if jmeter_available:
            # 在后台启动JMeter执行，不等待结果
            command = [
                "jmeter",
                "-n",
                "-t",
                str(jmx_path),
                "-l",
                str(output_path),
                "-Jjmeter.save.saveservice.output_format=csv",
                "-Jjmeter.save.saveservice.response_data=false",
                "-Jjmeter.save.saveservice.samplerData=false",
                "-Jjmeter.save.saveservice.requestHeaders=false",
                "-Jjmeter.save.saveservice.responseHeaders=false",
            ]
            logger.info(f"Starting JMeter command in background: {' '.join(command)}")

            # 启动后台任务
            asyncio.create_task(execute_jmeter_background(task_id, command, output_path))

            message = "JMeter execution started in background"
        else:
            # 模拟JMeter执行，创建虚拟JTL文件
            logger.warning("JMeter not found in system PATH, using dummy execution")
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
            # 对于模拟执行，立即标记为完成
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["cost_time"] = "0.15s"
            tasks_db[task_id]["completed_at"] = datetime.now().isoformat()
            save_tasks_data(tasks_db)
            message = "JMeter execution completed (simulated - JMeter not found)"

        # 立即返回任务信息，不等待完成
        return APIResponse(
            success=True,
            message=message,
            data=tasks_db[task_id],
            timestamp=datetime.utcnow().isoformat(),
        )

    except subprocess.TimeoutExpired:
        logger.error("JMeter execution timeout")
        return APIResponse(success=False, message="JMeter execution timed out", timestamp=datetime.utcnow().isoformat())
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
async def list_files(file_type: str = "jmx", search: Optional[str] = None):
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
                # Apply search filter if search term is provided
                if search and search.strip():
                    search_term = search.strip().lower()
                    filename_lower = file_path.name.lower()
                    # Fuzzy search: check if search term is contained in filename
                    if search_term not in filename_lower:
                        continue

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


@app.post("/generate-report/{task_id}")
async def generate_html_report(task_id: str):
    """Generate HTML report from JTL file."""
    try:
        import shutil
        import subprocess

        # Find task info
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")

        task = tasks_db[task_id]
        if task["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed")

        # Find corresponding JTL file
        output_file = task.get("output_file")
        if not output_file:
            raise HTTPException(status_code=404, detail="No JTL file found for this task")

        jtl_path = Path("jtl_files") / output_file
        if not jtl_path.exists():
            raise HTTPException(status_code=404, detail="JTL file not found")

        # Create report directory
        report_dir_name = jtl_path.stem
        report_dir = Path("reports") / report_dir_name

        # Remove existing report directory if exists
        if report_dir.exists():
            shutil.rmtree(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        # Check if JMeter is available
        jmeter_available = (
            os.path.exists("/opt/homebrew/bin/jmeter")
            or os.path.exists("/usr/local/bin/jmeter")
            or shutil.which("jmeter") is not None
        )

        logger.info(f"Report generation - JMeter availability check: {jmeter_available}")
        if jmeter_available:
            # Use real JMeter to generate HTML report
            command = ["jmeter", "-g", str(jtl_path), "-o", str(report_dir)]
            logger.info(f"Generating HTML report with command: {' '.join(command)}")

            result = subprocess.run(command, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(f"HTML report generated successfully: {report_dir}")

                # Update task with report path
                tasks_db[task_id]["report_path"] = f"/reports/{report_dir_name}/"
                save_tasks_data(tasks_db)

                return APIResponse(
                    success=True,
                    message="HTML report generated successfully",
                    data={
                        "task_id": task_id,
                        "report_path": f"/reports/{report_dir_name}/",
                        "message": "HTML report generated successfully",
                    },
                    timestamp=datetime.utcnow().isoformat(),
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
                    <p>Generated from: {output_file}</p>
                    <p>Task ID: {task_id}</p>
                    <p>Original File: {task['file_name']}</p>
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

            # Update task with report path
            tasks_db[task_id]["report_path"] = f"/reports/{report_dir_name}/"
            save_tasks_data(tasks_db)

            return APIResponse(
                success=True,
                message="Mock HTML report generated (JMeter not found)",
                data={
                    "task_id": task_id,
                    "report_path": f"/reports/{report_dir_name}/",
                    "message": "Mock HTML report generated",
                },
                timestamp=datetime.utcnow().isoformat(),
            )

    except subprocess.TimeoutExpired:
        logger.error("HTML report generation timeout")
        return APIResponse(success=False, message="Report generation timed out", timestamp=datetime.utcnow().isoformat())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate HTML report error: {e}")
        return APIResponse(success=False, message=str(e), timestamp=datetime.utcnow().isoformat())


@app.get("/download-report-zip/{task_id}")
async def download_html_report_zip(task_id: str):
    """Download HTML report as ZIP file."""
    try:
        import tempfile
        import zipfile

        # Find task info
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")

        task = tasks_db[task_id]
        if task["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed")

        # 使用任务中的真实report_path
        report_path = task.get("report_path")
        if not report_path:
            raise HTTPException(status_code=404, detail="No report available for this task")

        # 从report_path提取目录名称 (去掉前缀/reports/和后缀/)
        if report_path.startswith("/reports/"):
            report_dir_name = report_path[9:]  # 去掉 "/reports/"
            if report_dir_name.endswith("/"):
                report_dir_name = report_dir_name[:-1]  # 去掉末尾的 "/"
        else:
            raise HTTPException(status_code=404, detail="Invalid report path")

        report_dir = Path("reports") / report_dir_name

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
            zip_filename = f"jmeter_report_{report_dir_name}.zip"

            # Clean up temp file after response
            def cleanup():
                try:
                    Path(zip_path).unlink()
                except Exception:
                    pass

            response = FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

            # Schedule cleanup
            import threading

            timer = threading.Timer(10.0, cleanup)
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

    logger.info("🚀 启动 JMeter Toolkit 开发服务器")
    logger.info("📖 API文档: http://localhost:8000/docs")
    logger.info("🔍 健康检查: http://localhost:8000/health")
    logger.info("💡 前端界面: http://localhost:3000 (需单独启动)")
    logger.info("⏹️  按 Ctrl+C 停止服务器")

    uvicorn.run("dev_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
