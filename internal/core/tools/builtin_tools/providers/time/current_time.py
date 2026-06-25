#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
当前时间获取工具

@Author :   Xinkang Wu
@Time   :   2026/6/22 20:36
@File   :   current_time.py
"""
from datetime import datetime
from typing import Any

from langchain_core.tools import BaseTool


class CurrentTimeTool(BaseTool):
    """一个用于获取当前时间的工具"""

    name: str = "current_time"
    description: str = "一个用于获取当前时间的工具"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """获取当前系统时间并进行格式化"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def current_time(**kwargs) -> BaseTool:
    """返回获取当前时间工具"""
    return CurrentTimeTool()
