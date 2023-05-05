import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from enum import Enum
from os.path import isfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

logger.add(
    sink=sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <4}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


app = FastAPI(title="Jmeter ToolKit")

app.mount("/view_report", StaticFiles(directory="reports", html=True), name="reports")


JMX_FILE_PATH = Path("jmx_files")
JTL_FILES_PATH = Path("jtl_files")


class ExecuteJmxResponse(BaseModel):
    output_file_path: str
    cost_time: str
    status: str
    output_file: str
    err: str = ""


class JMeterManager:
    def __init__(self, jmx_file_path: Path, jtl_files_path: Path):
        self.jmx_file_path = jmx_file_path
        self.jtl_files_path = jtl_files_path

    def upload_jmx(self, jmx_file: UploadFile):
        if not jmx_file.filename.endswith(".jmx"):
            raise HTTPException(status_code=400, detail="Only JMX files are allowed")

        file_path = self.jmx_file_path / jmx_file.filename
        with open(file_path, "wb") as f:
            f.write(jmx_file.file.read())
        return {"file_name": jmx_file.filename, "file_path": str(file_path.absolute())}

    def execute_jmx(self, file_name: str) -> ExecuteJmxResponse:
        if not file_name.endswith(".jmx"):
            raise HTTPException(status_code=400, detail="Only JMX files are allowed")
        date_time_str: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file: str = f"{file_name.split('.')[0]}-{date_time_str}.jtl"
        output_path: Path = self.jtl_files_path / output_file
        logger.info(f"Output jtl file path: {output_path}")
        jmx_file: Path = self.jmx_file_path / file_name
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

    def generate_html_report_by_jtl_file(
        self, jtl_file: str, is_delete_exists_report: bool = True
    ) -> Path:
        if not jtl_file.endswith(".jtl"):
            raise HTTPException(status_code=400, detail="Only JTL files are allowed")
        jtl_file: Path = self.jtl_files_path / jtl_file
        if not jtl_file.exists():
            raise HTTPException(
                status_code=404, detail=f"jtl file not exists, {jtl_file.absolute()=}"
            )

        report_dir: Path = Path("reports") / jtl_file.stem
        if is_delete_exists_report and report_dir.exists():
            logger.info(f"report dir exists, remove it: {report_dir}")
            shutil.rmtree(report_dir)

        # use jmeter generate html report
        command = f"jmeter -g {jtl_file} -o {report_dir}"
        logger.info(f"generate html report command: {command}")
        subprocess.run(command, shell=True, check=True)

        return report_dir


def get_jmeter_manager():
    return JMeterManager(JMX_FILE_PATH, JTL_FILES_PATH)


@app.post("/upload_jmx")
async def upload_jmx(
    jmx_file: UploadFile = File(...),
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager),
):
    return jmeter_manager.upload_jmx(jmx_file)


@app.post("/execute_jmx", response_model=ExecuteJmxResponse)
def execute_jmx(
    file_name: str, jmeter_manager: JMeterManager = Depends(get_jmeter_manager)
) -> ExecuteJmxResponse:
    return jmeter_manager.execute_jmx(file_name)


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
    jmeter_manager: JMeterManager = Depends(get_jmeter_manager),
):
    # 1. Upload JMX file
    upload_result = jmeter_manager.upload_jmx(jmx_file)
    file_name = upload_result["file_name"]

    # 2. Execute JMX
    execute_result: ExecuteJmxResponse = jmeter_manager.execute_jmx(file_name)
    if execute_result.status == "failed":
        return execute_result

    # 3. Generate HTML report
    output_file = execute_result.output_file
    report_html_response: Path = jmeter_manager.generate_html_report_by_jtl_file(
        output_file
    )
    return {"report_url": f"{request.base_url}view_report/{report_html_response.name}"}


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
    elif file_type == FileType.jtl:
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
