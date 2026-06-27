#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置工具服务

@Author :   Xinkang Wu
@Time   :   2026/6/23 21:58
@File   :   builtin_tool_service.py
"""
import mimetypes
import os
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject
from pydantic import BaseModel

from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""

    builtin_provider_manager: BuiltinProviderManager
    builtin_category_manager: BuiltinCategoryManager

    def get_builtin_tools(self) -> list:
        """获取所有内置工具信息"""

        # 获取所有内置服务提供商
        providers = self.builtin_provider_manager.get_providers()

        builtin_tools = []
        # 遍历所有服务提供商
        for provider in providers:
            # 获取服务提供商实体
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude={"icon"}),  # 排除icon属性，前端直接根据服务提供商名称获取
                "tools": [],
            }

            # 遍历该服务提供商的所有工具实体
            for tool_entity in provider.get_tool_entities():
                # 获取工具函数
                tool = provider.get_tool(tool_entity.name)
                tool_dict = {
                    **tool_entity.model_dump(),
                    # 获取工具的大模型输入参数
                    "inputs": self.get_tool_inputs(tool)
                }
                builtin_tool["tools"].append(tool_dict)
            builtin_tools.append(builtin_tool)

        return builtin_tools

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据服务提供商名称和工具名称，获取工具信息"""

        # 获取服务提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该服务提供商{provider_name}不存在")

        # 获取该服务提供商的对应工具实体
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"该工具{tool_name}不存在")

        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)

        builtin_tool = {
            "provider": {**provider_entity.model_dump(exclude={"icon", "created_at"})},
            **tool_entity.model_dump(),
            "created_at": provider_entity.created_at,
            "inputs": self.get_tool_inputs(tool)
        }

        return builtin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """获取服务提供商的icon文件"""

        # 获取服务提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该服务提供商{provider_name}不存在")

        # 获取项目的根路径
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        # 拼接服务提供商的路径
        provider_path = os.path.join(
            root_path,
            "internal", "core", "tools", "builtin_tools", "providers", provider_name
        )

        # 拼接服务提供商的icon文件路径
        icon_path = os.path.join(provider_path, "_asset", provider.provider_entity.icon)

        # 检测icon文件是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(
                f"该服务提供商{provider_name}的_assert目录下找不到图标文件{provider.provider_entity.icon}")

        # 获取icon文件的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 获取icon的字节数据
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def get_categories(self) -> list[dict[str, Any]]:
        """获取所有服务提供商的分类信息"""

        category_map = self.builtin_category_manager.get_category_map()
        return [{
            "name": category["entity"].name,
            "category": category["entity"].category,
            "icon": category["icon"]
        } for category in category_map.values()]

    @classmethod
    def get_tool_inputs(cls, tool) -> list:
        """获取工具的大模型输入参数"""

        inputs = []
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
            # 遍历该工具函数的Pydantic Field参数
            for field_name, field_info in tool.args_schema.model_json_schema()["properties"].items():
                input = {
                    "name": field_name,
                    "description": field_info.get("description", ""),
                    "required": field_info.get("required", True),
                    "type": field_info["type"],
                }
                inputs.append(input)
        return inputs
