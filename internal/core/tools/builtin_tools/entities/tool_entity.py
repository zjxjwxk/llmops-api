#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具实体类

@Author :   Xinkang Wu
@Time   :   2026/6/21 15:42
@File   :   tool_entity.py
"""
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class ToolParamType(str, Enum):
    """工具参数类型枚举"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"


class ToolParam(BaseModel):
    """工具参数类"""

    name: str  # 名称
    label: str  # 标签
    type: ToolParamType  # 类型
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 默认值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    options: list[dict[str, Any]] = Field(default_factory=list)  # 可选项列表


class ToolEntity(BaseModel):
    """工具实体类，映射工具配置信息文件"""

    name: str  # 名称
    label: str  # 标签
    description: str  # 描述
    params: list[ToolParam] = Field(default_factory=list)  # 参数列表
