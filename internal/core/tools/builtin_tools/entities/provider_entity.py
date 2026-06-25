#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务提供商实体类

@Author :   Xinkang Wu
@Time   :   2026/6/21 15:32
@File   :   provider_entity.py
"""
import os.path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from internal.lib.helper import dynamic_import
from .tool_entity import ToolEntity


class ProviderEntity(BaseModel):
    """服务提供商实体，映射服务提供商配置文件"""

    name: str  # 名称
    label: str  # 标签
    description: str  # 描述
    icon: str  # 图标地址
    background: str  # 图标颜色
    category: str  # 分类
    created_at: int = 0  # 创建时间戳


class Provider(BaseModel):
    """服务提供商，包含服务提供商的工具映射"""

    name: str  # 名称
    position: int  # 顺序
    provider_entity: ProviderEntity  # 实体
    tool_entity_map: dict[str, ToolEntity] = Field(default_factory=dict)  # 工具实体映射
    tool_func_map: dict[str, Any] = Field(default_factory=dict)  # 工具函数映射

    def __init__(self, **kwargs):
        """构造函数，初始化服务提供商的工具映射"""

        super().__init__(**kwargs)
        self._init_provider()

    class Config:
        """Pydantic用于定义被保护的（不可用的）字段名称"""
        protected_namespaces = ()

    def get_tool(self, tool_name: str) -> Any:
        """根据工具名称，获取工具函数"""
        return self.tool_func_map.get(tool_name)

    def get_tool_entity(self, tool_name: str) -> ToolEntity:
        """根据工具名称，获取工具实体"""
        return self.tool_entity_map.get(tool_name)

    def get_tool_entities(self) -> list[ToolEntity]:
        """获取该服务提供商的所有工具实体"""
        return list(self.tool_entity_map.values())

    def _init_provider(self):
        """初始化服务提供商的工具映射"""

        # 获取服务提供商文件夹路径
        current_path = os.path.abspath(__file__)
        entities_folder_path = os.path.dirname(current_path)
        provider_folder_path = os.path.join(os.path.dirname(entities_folder_path), "providers", self.name)

        # 读取工具顺序配置
        positions_yaml_path = os.path.join(provider_folder_path, "positions.yaml")
        with open(positions_yaml_path, encoding="utf-8") as f:
            positions_yaml_data = yaml.safe_load(f)

        # 按顺序遍历工具名称
        for tool_name in positions_yaml_data:
            # 读取工具配置
            tool_yaml_path = os.path.join(provider_folder_path, f"{tool_name}.yaml")
            with open(tool_yaml_path, encoding="utf-8") as f:
                tool_yaml_data = yaml.safe_load(f)

            # 更新工具实体映射
            self.tool_entity_map[tool_name] = ToolEntity(**tool_yaml_data)

            # 更新工具函数映射（动态导入工具）
            self.tool_func_map[tool_name] = dynamic_import(f"internal.core.tools.builtin_tools.providers.{self.name}",
                                                           tool_name)
