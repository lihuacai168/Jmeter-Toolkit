# !/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel

from core.cache import Cache


class RunCmdResp(BaseModel):
    pid: int
    stdout: str
    stderr: str
    returncode: int


class ExecuteJmxResponse(BaseModel):
    output_file_path: str
    cost_time: str
    status: str
    output_file: str
    err: str = ""
    run_cmd_resp: RunCmdResp = None


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

    def execute_jmx(self, file_name: str, cache: Cache) -> ExecuteJmxResponse:
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
            result: RunCmdResp = self.run_cmd(command, cache=cache, cache_key=output_file)
            cost_time = datetime.now() - now
            logger.info(f"Cost time: {cost_time}")

            if result.returncode == 0:
                return ExecuteJmxResponse(
                    output_file_path=str(output_path.absolute()),
                    cost_time=f"{cost_time.total_seconds():.2f}s",
                    status="success",
                    output_file=output_file,
                    run_cmd_resp=result,
                )
            else:
                logger.error(
                    f"Command '{command}' returned non-zero exit status {result.returncode}"
                )
                return ExecuteJmxResponse(
                    output_file_path="",
                    cost_time=0,
                    status="failed",
                    output_file="",
                    err=f"returned non-zero exit status {result.returncode}",
                    run_cmd_resp=result,
                )

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Command '{e.cmd}' returned non-zero exit status {traceback.format_exc()}"
            )
            return ExecuteJmxResponse(
                output_file_path="",
                cost_time=0,
                status="failed",
                output_file="",
                err=traceback.format_exc(),
                run_cmd_resp=None,
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
        docker_compose_dict["networks"] = {
            "default": {"name": f"jmeter-{project_name}"}
        }

        with open(docker_compose_file, "w") as f:
            yaml.dump(docker_compose_dict, f)

        return docker_compose_file

    @staticmethod
    def run_distributed_jmeter(
        docker_compose_file: str, project_name: str
    ) -> RunCmdResp:
        logger.info(f"docker compose file: {docker_compose_file}")
        command = f"docker-compose -p {project_name} -f {docker_compose_file} up  -d"
        return JMeterManager.run_cmd(command)

    @staticmethod
    def stop_distributed_jmeter(
        docker_compose_file: str, project_name: str
    ) -> RunCmdResp:
        command = f"docker-compose -p {project_name} -f {docker_compose_file} down"
        return JMeterManager.run_cmd(command)

    @staticmethod
    def run_cmd(command: str, cache: Cache = None, cache_key: str = "") -> RunCmdResp:
        logger.info(f"run jmeter command: {command}")
        proc: subprocess.Popen = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid
        )

        if cache and cache_key:
            logger.info(f"Set cache key: {cache_key}, value: {proc.pid}")
            cache.set(cache_key, proc.pid)

        logger.info(f"jmeter process: {proc.pid=}")
        stdout, stderr = proc.communicate()
        if stdout:
            logger.info(f"stdout: {stdout.decode()}")
        if stderr:
            logger.info(f"stderr: {stderr.decode()}")
        proc.wait()
        if proc.returncode != 0:
            logger.error(f"Command failed with exit code {proc.returncode}")
        else:
            logger.info(f"Command completed successfully")
        return RunCmdResp(
            pid=proc.pid, stdout=stdout, stderr=stderr, returncode=proc.returncode
        )


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
