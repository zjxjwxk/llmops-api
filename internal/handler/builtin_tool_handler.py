#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置工具处理器

@Author :   Xinkang Wu
@Time   :   2026/6/23 21:51
@File   :   builtin_tool_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.service import BuiltinToolService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理器"""

    builtin_tool_service: BuiltinToolService

    def get_builtin_tools(self):
        """获取所有内置工具信息+服务提供商信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        return success_json(builtin_tools)

    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据提供商名称+工具名称，获取工具信息"""
        builtin_tool = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(builtin_tool)
