#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务提供商工厂类

@Author :   Xinkang Wu
@Time   :   2026/6/21 15:13
@File   :   builtin_provider_manager.py
"""
import os.path
from typing import Any

import yaml
from injector import singleton, inject

from internal.core.tools.builtin_tools.entities import ProviderEntity, Provider


@inject
@singleton
class BuiltinProviderManager:
    """内置服务提供商管理类"""

    # 服务提供商Map
    provider_map: dict[str, Provider] = {}

    def __init__(self):
        """构造函数，初始化服务提供商Map"""
        self._init_provider_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据服务提供商名称，获取服务提供商"""
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        """获取所有服务提供商"""
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        """获取所有服务提供商实体"""
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str) -> Any:
        """根据服务提供商名称和工具名称，获取特定工具"""
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.get_tool(tool_name)

    def _init_provider_map(self):
        """初始化服务提供商Map"""

        # 检查Map是否不为空
        if self.provider_map:
            return

        # 获取服务提供商配置文件路径
        current_path = os.path.abspath(__file__)
        providers_folder_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(providers_folder_path, "providers.yaml")

        # 读取服务提供商配置文件
        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        # 遍历服务提供商配置
        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)

            # 初始化服务提供商Map
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity,
            )
