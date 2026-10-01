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

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.api_tool_schema import ValidateOpenAPISchemaReq, CreateApiToolReq, GetApiToolProviderResp, \
    GetApiToolResp, GetApiToolProvidersWithPageReq, GetApiToolProvidersWithPageResp, UpdateApiToolProviderReq
from internal.service import ApiToolService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """自定义API工具处理器"""

    api_tool_service: ApiToolService

    @login_required
    def validate_openapi_schema(self):
        """校验OpenAPI Schema字符串"""

        # 提取请求并校验
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务解析OpenAPI Schema字符串
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        return success_message("OpenAPI Schema校验通过")

    @login_required
    def create_api_tool_provider(self):
        """创建自定义API工具提供商"""

        # 提取请求并校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建API工具
        self.api_tool_service.create_api_tool_provider(req, current_user)

        return success_message("创建自定义API插件成功")

    @login_required
    def get_api_tool_provider(self, provider_id: UUID):
        """获取自定义API工具提供商"""

        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id, current_user)

        resp = GetApiToolProviderResp()

        return success_json(resp.dump(api_tool_provider))

    @login_required
    def get_api_tool_providers_with_page(self):
        """获取自定义API工具提供商分页"""

        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_provider, paginator = self.api_tool_service.get_api_tool_providers_with_page(req, current_user)

        resp = GetApiToolProvidersWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(api_tool_provider), paginator=paginator))

    @login_required
    def update_api_tool_provider(self, provider_id: UUID):
        """更新自定义API工具提供商"""

        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(provider_id, req, current_user)

        return success_message("更新自定义API插件成功")

    @login_required
    def delete_api_tool_provider(self, provider_id: UUID):
        """删除自定义API工具提供商"""

        self.api_tool_service.delete_api_tool_provider(provider_id, current_user)

        return success_message("删除自定义API插件成功")

    @login_required
    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """获取自定义API工具"""

        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name, current_user)

        resp = GetApiToolResp()

        return success_json(resp.dump(api_tool))
