#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置工具分类管理类

@Author :   Xinkang Wu
@Time   :   2026/6/26 21:10
@File   :   builtin_category_manager.py
"""
import os
from typing import Any

import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


@inject
@singleton
class BuiltinCategoryManager(BaseModel):
    """内置工具分类管理器"""

    category_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        """构造函数，初始化分类Map"""
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        """获取分类Map"""
        return self.category_map

    def _init_categories(self):
        """初始化分类Map"""

        # 检查Map是否已初始化
        if self.category_map:
            return

        # 获取分类配置文件路径
        current_path = os.path.abspath(__file__)
        categories_folder_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(categories_folder_path, "categories.yaml")

        with open(categories_yaml_path, encoding="utf-8") as f:
            categories_data = yaml.safe_load(f)

        # 遍历分类配置
        for category in categories_data:
            category_entity = CategoryEntity(**category)

            # 获取icon文件的路径，并检查文件是否存在
            icon_path = os.path.join(categories_folder_path, "icons", category_entity.icon)
            if not os.path.exists(icon_path):
                raise NotFoundException(f"该分类{category_entity.category}的icon文件{category_entity.icon}不存在")

            # 读取icon文件
            with open(icon_path, encoding="utf-8") as f:
                icon = f.read()

            # 更新分类Map
            self.category_map[category_entity.category] = {
                "entity": category_entity,
                "icon": icon,
            }
