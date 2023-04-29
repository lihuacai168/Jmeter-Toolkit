import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime
from enum import Enum
from os.path import isfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

logger.add(
    sink=sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <4}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

app = FastAPI()

JMX_FILE_PATH = Path("jmx_files")
JTL_FILES_PATH = Path("jtl_files")



class ExecuteJmxResponse(BaseModel):
    output_file_path: str
    cost_time: str
    status: str
    output_file: str
    err: str = ""


@app.post("/upload_jmx")
async def upload_jmx(jmx_file: UploadFile = File(...)):
    if not jmx_file.filename.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="Only JMX files are allowed")

    file_path = JMX_FILE_PATH / jmx_file.filename
    with open(file_path, "wb") as f:
        f.write(await jmx_file.read())
    return {"file_name": jmx_file.filename, "file_path": str(file_path.absolute())}


@app.post("/execute_jmx", response_model=ExecuteJmxResponse)
def execute_jmx(file_name: str) -> ExecuteJmxResponse:
    if not file_name.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="Only JMX files are allowed")
    date_time_str: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file: str = f"{file_name.split('.')[0]}-{date_time_str}.jtl"
    output_path: Path = JTL_FILES_PATH / output_file
    logger.info(f"Output jtl file path: {output_path}")
    jmx_file: Path = JMX_FILE_PATH / file_name
    command: str = f"jmeter -n -t {jmx_file} -l {output_path}"
    logger.info(f"{command=}")
    now = datetime.now()
    try:
        result = subprocess.run(command, shell=True, check=True)
        cost_time = datetime.now() - now
        logger.info(f"Cost time: {cost_time}")

        if result.returncode == 0:
            return ExecuteJmxResponse(
                output_file_path=str(output_path.absolute()),
                cost_time=f"{cost_time.total_seconds():.2f}s",
                status="success",
                output_file=output_file,
            )
        else:
            logger.error(
                f"Command '{result.cmd}' returned non-zero exit status {result.returncode}"
            )
            return ExecuteJmxResponse(
                output_file_path="",
                cost_time=cost_time,
                status="failed",
                output_file="",
                err=f"returned non-zero exit status {result.returncode}",
            )

    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command '{e.cmd}' returned non-zero exit status {traceback.format_exc()}"
        )
        return ExecuteJmxResponse(
            output_file_path="",
            cost_time=cost_time,
            status="failed",
            output_file="",
            err=traceback.format_exc(),
        )


@app.get("/report/{output_file_path}")
def generate_html_report_by_jtl_file(jtl_file: str):
    if not jtl_file.endswith(".jtl"):
        raise HTTPException(status_code=400, detail="Only JTL files are allowed")
    jtl_file: Path = JTL_FILES_PATH / jtl_file
    if not jtl_file.exists():
        raise HTTPException(
            status_code=404, detail=f"jtl file not exists, {jtl_file.absolute()=}"
        )

    temp_dir = tempfile.mkdtemp()

    # use jmeter generate html report
    command = f"jmeter -g {jtl_file} -o {temp_dir}"
    logger.info(f"generate html report command: {command}")
    subprocess.run(command, shell=True, check=True)

    report_file = os.path.join(temp_dir, "index.html")

    with open(report_file, "r") as f:
        report_html = f.read()

    app.mount("/report", StaticFiles(directory=temp_dir), name="reports")

    return HTMLResponse(content=report_html)


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

    files = [f for f in os.listdir(dir_path) if isfile(os.path.join(dir_path, f)) and f.endswith(ext)]
    return {"files": files}


@app.get("/files/{filename}")
async def get_file_content(filename: str, file_type: FileType):
    if file_type == FileType.jmx:
        file = JMX_FILE_PATH / filename
    elif file_type == FileType.jtl:
        file = JTL_FILES_PATH / filename
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file.exists():
        raise HTTPException(status_code=404, detail=f"File not found, file={file.absolute()}")

    with open(file, "r") as f:
        content = f.read()

    return {"filename": filename, "content": content}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
