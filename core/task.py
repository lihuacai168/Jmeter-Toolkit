# !/usr/bin/python3
# -*- coding: utf-8 -*-

# @Author: 花菜
# @File: task.py
# @Time : 2023/5/12 17:51
# @Email: lihuacai168@gmail.com
import os
import signal
import traceback

from loguru import logger

from core.cache import Cache
from core.jmeter import ExecuteJmxResponse, JMeterManager, RunCmdResp


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


@singleton
class TaskManger:
    def __init__(self, jmeter_manager: JMeterManager, cache: Cache):
        self.jmeter_manager = jmeter_manager
        self.cache = cache

    def execute_jmx(self, file_name: str) -> ExecuteJmxResponse:
        execute_result: ExecuteJmxResponse = self.jmeter_manager.execute_jmx(
            file_name=file_name, cache=self.cache
        )
        return execute_result

    def list_tasks(self) -> dict:
        return self.cache.get_all_tasks()

    @staticmethod
    def _stop_task_by_id(pid: int):
        os.killpg(os.getpgid(pid), signal.SIGTERM)

    def stop_task_by_file_name(self, file_name: str) -> RunCmdResp:
        pid: int = self.cache.get(file_name)
        if pid:
            try:
                logger.info(f"start to stop {file_name=} {pid=}")
                self._stop_task_by_id(pid)
                logger.info(f"stop {file_name=} {pid=} success")
                logger.info(f"start to remove cache {file_name=} {pid=}")
                self.cache.remove(file_name)
                logger.info(f"remove cache {file_name=} {pid=} success")
            except Exception as e:
                logger.error(f"stop {file_name=} {pid=} fail {traceback.format_exc()}")
                return RunCmdResp(
                    pid=pid,
                    returncode=1,
                    stdout="",
                    stderr=f"stop {pid=} fail {traceback.format_exc()}",
                )
            return RunCmdResp(
                pid=pid,
                returncode=0,
                stdout="success",
                stderr="",
            )

        else:
            return RunCmdResp(
                pid=0,
                returncode=1,
                stdout="",
                stderr=f"no found {file_name=} in cache",
            )

    def stop_all(self) -> RunCmdResp:
        keys: list[str] = list(self.list_tasks().keys())
        return [self.stop_task_by_file_name(file_name=key) for key in keys]
