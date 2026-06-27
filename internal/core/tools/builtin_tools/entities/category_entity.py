#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分类实体类

@Author :   Xinkang Wu
@Time   :   2026/6/26 21:26
@File   :   category_entity.py
"""
from pydantic import BaseModel, field_validator

from internal.exception import FailException


class CategoryEntity(BaseModel):
    # 分类实体，映射分类配置文件

    category: str  # 分类唯一标识
    name: str  # 分类名称
    icon: str  # 图标名称

    @field_validator("icon")
    @classmethod
    def check_icon_extension(cls, value: str):
        """校验icon文件的扩展名"""

        if not value.endswith(".svg"):
            raise FailException(f"仅支持svg格式的icon文件，当前文件扩展名为{value}")
        return value
