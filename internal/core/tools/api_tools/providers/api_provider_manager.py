#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具提供商管理器

@Author :   Xinkang Wu
@Time   :   2026/7/5 14:56
@File   :   api_provider_manager.py
"""
from dataclasses import dataclass
from typing import Type, Optional, Callable

import requests
from injector import inject
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from internal.core.tools.api_tools.entities import ToolEntity, ParameterTypeMap, ParameterIn


@inject
@dataclass
class ApiProviderManager(BaseModel):
    """自定义API工具提供者管理器，根据自定义工具配置生成LangChain工具"""

    @classmethod
    def _create_tool_func_from_tool_entity(cls, tool_entity: ToolEntity) -> Callable:
        """根据自定义API工具实体，构建工具函数"""

        def tool_func(**kwargs) -> str:
            """自定义API工具函数闭包，根据外部传入的工具实体，构建工具函数"""

            # 存储不同位置的参数字典，便于发起request的参数传递
            parameters_in = {
                ParameterIn.PATH: {},
                ParameterIn.QUERY: {},
                ParameterIn.HEADER: {},
                ParameterIn.COOKIE: {},
                ParameterIn.REQUEST_BODY: {}
            }

            # 构建工具参数和请求头字典
            parameter_map = {parameter.get("name"): parameter for parameter in tool_entity.parameters}
            header_map = {header.get("key"): header.get("value") for header in tool_entity.headers}

            # 校验输入参数并存入对应位置的参数字典
            for key, value in kwargs.items():
                parameter = parameter_map.get(key)
                if parameter is None:
                    continue

                parameters_in[parameter.get("in", ParameterIn.QUERY)][key] = value

            return requests.request(
                method=tool_entity.method,
                url=tool_entity.url.format(**parameters_in[ParameterIn.PATH]),
                params=parameters_in[ParameterIn.QUERY],
                json=parameters_in[ParameterIn.REQUEST_BODY],
                headers={**header_map, **parameters_in[ParameterIn.HEADER]},
                cookies=parameters_in[ParameterIn.COOKIE]
            ).text

        return tool_func

    @classmethod
    def _create_model_from_parameters(cls, parameters: list[dict]) -> Type[BaseModel]:
        """根据自定义API工具的parameters参数，构建Pydantic BaseModel子类作为args_schema"""

        fields = {}
        for parameter in parameters:
            field_name = parameter.get("name")
            field_type = ParameterTypeMap.get(parameter.get("type"), str)
            field_required = parameter.get("required", True)
            field_description = parameter.get("description", "")

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description)
            )

        return create_model("DynamicModel", **fields)

    def get_tool(self, tool_entity: ToolEntity) -> BaseTool:
        """根据自定义API工具实体生成LangChain工具"""

        return StructuredTool.from_function(
            func=self._create_tool_func_from_tool_entity(tool_entity),
            name=f"api_tool_{tool_entity.id}_{tool_entity.name}",
            description=tool_entity.description,
            args_schema=self._create_model_from_parameters(tool_entity.parameters),
        )
