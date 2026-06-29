#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具处理器

@Author :   Xinkang Wu
@Time   :   2026/6/28 15:51
@File   :   api_tool_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.api_tool_schema import ValidateOpenAPISchemaReq, CreateApiToolReq, GetApiToolProviderResp, \
    GetApiToolResp
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """自定义API工具处理器"""

    api_tool_service: ApiToolService

    def create_api_tool(self):
        """创建自定义API工具"""

        # 提取请求并校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建API工具
        self.api_tool_service.create_api_tool(req)

        return success_message("创建自定义API插件成功")

    def get_api_tool_provider(self, provider_id: UUID):
        """获取自定义API工具提供商的信息"""

        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()

        return success_json(resp.dump(api_tool_provider))

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """获取自定义API工具的信息"""

        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)

        resp = GetApiToolResp()

        return success_json(resp.dump(api_tool))

    def validate_openapi_schema(self):
        """校验OpenAPI Schema字符串"""

        # 提取请求并校验
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务解析OpenAPI Schema字符串
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        return success_message("OpenAPI Schema校验通过")
