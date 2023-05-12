import os
import sys
from enum import Enum
from os.path import isfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from loguru import logger
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from core.cache import DictCache
from core.jmeter import ExecuteJmxResponse, JMeterManager, RunCmdResp
from core.task import TaskManger

# logger.add(
#     sink=sys.stderr,
#     format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#     "<level>{level: <4}</level> | "
#     "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
#     level="INFO",
# )

app = FastAPI(title="Jmeter ToolKit")

app.mount("/view_report", StaticFiles(directory="reports", html=True), name="reports")

JMX_FILE_PATH = Path("jmx_files")
JTL_FILES_PATH = Path("jtl_files")


def get_jmeter_manager():
    return JMeterManager(JMX_FILE_PATH, JTL_FILES_PATH)


def get_cache():
    return DictCache()


def get_task_manager() -> TaskManger:
    return TaskManger(jmeter_manager=get_jmeter_manager(), cache=get_cache())


@app.post("/upload_jmx")
async def upload_jmx(
    jmx_file: UploadFile = File(...),
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager),
):
    return jmeter_manager.upload_jmx(jmx_file)


@app.post("/execute_jmx", response_model=ExecuteJmxResponse)
def execute_jmx(
    file_name: str,
    task_manager: TaskManger = Depends(get_task_manager),
) -> ExecuteJmxResponse:
    return task_manager.execute_jmx(file_name)


@app.get("/report/{output_file_path}")
def generate_html_report_by_jtl_file(
    request: Request,
    jtl_file: str,
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager),
):
    report_html_response: Path = jmeter_manager.generate_html_report_by_jtl_file(
        jtl_file
    )
    return {"report_url": f"{request.base_url}view_report/{report_html_response.name}"}


@app.post("/upload_execute_report")
def upload_execute_report(
    request: Request,
    jmx_file: UploadFile = File(...),
    task_manager: TaskManger = Depends(get_task_manager),
):
    # 1. Upload JMX file
    upload_result = task_manager.jmeter_manager.upload_jmx(jmx_file)
    file_name = upload_result["file_name"]

    # 2. Execute JMX
    execute_result: ExecuteJmxResponse = task_manager.execute_jmx(file_name)
    if execute_result.status == "failed":
        return execute_result

    # 3. Generate HTML report
    output_file = execute_result.output_file
    report_html_response: Path = (
        task_manager.jmeter_manager.generate_html_report_by_jtl_file(output_file)
    )
    return {
        "report_url": f"{request.base_url}view_report/{report_html_response.name}",
        "execute_result": execute_result,
    }


@app.get("/tasks", response_model=dict)
def list_tasks(task_manager: TaskManger = Depends(get_task_manager)):
    return task_manager.list_tasks()


@app.get("/stop_task_by_jtl_file/{jtl_file}", response_model=RunCmdResp)
def stop_task_by_file_name(
    jtl_file: str, task_manager: TaskManger = Depends(get_task_manager)
):
    return task_manager.stop_task_by_file_name(jtl_file)


@app.get("/stop_all_tasks", response_model=list[RunCmdResp])
def stop_all_tasks(task_manager: TaskManger = Depends(get_task_manager)):
    return task_manager.stop_all()


class FileType(str, Enum):
    jmx = "jmx"
    jtl = "jtl"


@app.get("/files")
async def list_files(file_type: FileType):
    if file_type == FileType.jmx:
        dir_path = "./jmx_files"
        ext = ".jmx"
    elif file_type == FileType.jtl:
        dir_path = "./jtl_files"
        ext = ".jtl"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    files = [
        f
        for f in os.listdir(dir_path)
        if isfile(os.path.join(dir_path, f)) and f.endswith(ext)
    ]
    return {"files": files}


@app.get("/files/{filename}")
async def get_file_content(filename: str, file_type: FileType):
    if file_type == FileType.jmx:
        file = JMX_FILE_PATH / filename
    elif file_type == FileType.e.jtl:
        file = JTL_FILES_PATH / filename
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file.exists():
        raise HTTPException(
            status_code=404, detail=f"File not found, file={file.absolute()}"
        )

    with open(file, "r") as f:
        content = f.read()

    return {"filename": filename, "content": content}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
