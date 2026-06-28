#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具服务类

@Author :   Xinkang Wu
@Time   :   2026/6/28 15:59
@File   :   api_tool_service.py
"""
import json
from dataclasses import dataclass

from injector import inject

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidationException


@inject
@dataclass
class ApiToolService:
    """自定义API工具服务"""

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析OpenAPI Schema字符串"""

        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception:
            raise ValidationException("OpenAPI Schema校验不通过")

        return OpenAPISchema(**data)
