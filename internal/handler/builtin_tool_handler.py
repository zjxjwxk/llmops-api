#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置工具处理器

@Author :   Xinkang Wu
@Time   :   2026/6/23 21:51
@File   :   builtin_tool_handler.py
"""
import io
from dataclasses import dataclass

from flask import send_file
from flask_login import login_required
from injector import inject

from internal.service import BuiltinToolService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理器"""

    builtin_tool_service: BuiltinToolService

    @login_required
    def get_builtin_tools(self):
        """获取所有内置工具信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        return success_json(builtin_tools)

    @login_required
    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据提供商名称+工具名称，获取工具信息"""
        builtin_tool = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(builtin_tool)

    def get_provider_icon(self, provider_name: str):
        """获取指定服务提供商icon"""
        icon, mimetype = self.builtin_tool_service.get_provider_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)

    @login_required
    def get_categories(self):
        """获取所有服务提供商的分类"""
        categories = self.builtin_tool_service.get_categories()
        return success_json(categories)
