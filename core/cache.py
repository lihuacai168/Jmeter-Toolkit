# !/usr/bin/python3
# -*- coding: utf-8 -*-

# @Author: 花菜
# @File: cache.py
# @Time : 2023/5/12 17:56
# @Email: lihuacai168@gmail.com

from abc import ABC, abstractmethod


class Cache:
    def __init__(self):
        ...

    @abstractmethod
    def get(self, key: str):
        ...

    @abstractmethod
    def set(self, key, value, ttl: int = -1):
        ...

    @abstractmethod
    def get_all_pid(self):
        pass

    @abstractmethod
    def get_all_tasks(self) -> dict:
        ...

    @abstractmethod
    def remove(self, key):
        pass


class DictCache(Cache, ABC):
    def __init__(self):
        super().__init__()
        self._cache = {}

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key, value, ttl: int = -1):
        self._cache[key] = value

    def get_all_pid(self) -> list[int]:
        return list(self._cache.values())

    def get_all_tasks(self) -> dict:
        return self._cache

    def remove(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
