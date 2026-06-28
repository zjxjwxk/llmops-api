#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAPI Schema实体类

@Author :   Xinkang Wu
@Time   :   2026/6/28 16:06
@File   :   openapi_schema.py
"""
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from internal.exception import ValidationException


class ParameterIn(str, Enum):
    """方法参数支持的位置"""
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    REQUEST_BODY = "request_body"


class ParameterType(str, Enum):
    """方法参数支持的类型"""
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


class OpenAPISchema(BaseModel):
    """OpenAPI Schema实体类"""

    description: str = Field(default="", validate_default=True, description="工具提供商的描述信息")
    server: str = Field(default="", validate_default=True, description="工具提供商的服务地址")
    paths: dict[str, dict] = Field(default_factory=dict, validate_default=True,
                                   description="工具提供商的服务路径字典（路径=>方法）")

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, description: str) -> str:
        """校验description"""
        if description is None or description == "":
            raise ValidationException("openapi_schema中的description不能为空")
        return description

    @field_validator("server", mode="before")
    @classmethod
    def validate_server(cls, server: str) -> str:
        """校验server"""
        if server is None or server == "":
            raise ValidationException("openapi_schema中的server不能为空")
        return server

    @field_validator("paths", mode="before")
    @classmethod
    def validate_paths(cls, paths: dict[str, dict]) -> dict:
        """校验paths"""

        if not paths or not isinstance(paths, dict):
            raise ValidationException("openapi_schema中的paths不能为空，且必须为字典类型")

        # 支持的HTTP方法
        supported_methods = ["get", "post"]

        # OpenAPI Schema中的操作列表(path/method/operation)
        operations = []

        # 解析得到的paths字典
        parsed_paths = {}

        # 遍历paths所有路径，提取对应方法和操作
        for path, path_methods in paths.items():
            for supported_method in supported_methods:
                if supported_method in path_methods:
                    # 更新操作列表
                    operations.append({
                        "path": path,
                        "method": supported_method,
                        "operation": path_methods[supported_method],
                    })

        # 遍历所有操作并校验各个字段
        operation_ids = []
        for operation in operations:
            # 校验description
            if not isinstance(operation["operation"].get("description"), str):
                raise ValidationException("openapi_schema的paths/method/operation的description不能为空")

            # 校验operationId
            if not isinstance(operation["operation"].get("operationId"), str):
                raise ValidationException("openapi_schema的paths/method/operation的operationId不能为空")

            # 校验operationId是否唯一
            if operation["operation"]["operationId"] in operation_ids:
                raise ValidationException(
                    f"openapi_schema的paths/method/operation的operationId必须唯一，{operation['operation']['operationId']}存在重复")

            operation_ids.append(operation["operation"]["operationId"])

            # 校验parameters
            if not isinstance(operation["operation"].get("parameters", []), list):
                raise ValidationException("openapi_schema的paths/method/operation的parameters必须为列表类型或为空")

            # 校验parameters格式
            for parameter in operation["operation"].get("parameters", []):
                # 校验name
                if not isinstance(parameter.get("name"), str):
                    raise ValidationException(
                        "openapi_schema的paths/method/operation/parameters的name不能为空且必须为字符串类型")

                # 校验in
                if (not isinstance(parameter.get("in"), str)
                        or parameter.get("in") not in ParameterIn.__members__.values()):
                    raise ValidationException(
                        f"openapi_schema的paths/method/operation/parameters的in必须为{'/'.join([item.value for item in ParameterIn])}")

                # 校验description
                if not isinstance(parameter.get("description"), str):
                    raise ValidationException(
                        "openapi_schema的paths/method/operation/parameters的description不能为空且必须为字符串类型")

                # 校验required
                if not isinstance(parameter.get("required"), bool):
                    raise ValidationException(
                        "openapi_schema的paths/method/operation/parameters的required不能为空且必须为布尔值类型")

                # 校验type
                if (not isinstance(parameter.get("type"), str)
                        or parameter.get("type") not in ParameterType.__members__.values()):
                    raise ValidationException(
                        f"openapi_schema的paths/method/operation/parameters的type必须为{'/'.join([item.value for item in ParameterType])}")

            # 组装paths字典
            parsed_paths[operation["path"]] = {
                operation["method"]: {
                    "description": operation["operation"]["description"],
                    "operationId": operation["operation"]["operationId"],
                    "parameters": [{
                        "name": parameter.get("name"),
                        "in": parameter.get("in"),
                        "description": parameter.get("description"),
                        "required": parameter.get("required"),
                        "type": parameter.get("type"),
                    } for parameter in operation["operation"].get("parameters", [])],
                }
            }

        return parsed_paths
