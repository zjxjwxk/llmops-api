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
from uuid import UUID

from injector import inject

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidationException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class ApiToolService:
    """自定义API工具服务"""

    db: SQLAlchemy

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

    def create_api_tool(self, req: CreateApiToolReq) -> None:
        """创建自定义API工具"""

        # TODO: 实现授权认证模块后，完善账户相关逻辑
        account_id = "05a9c691-a5b0-4661-893a-430c760eb8cd"

        # 检验并提取openapi_schema
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 判断该工具提供商名称是否已存在于当前账户
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data,
        ).one_or_none()

        if api_tool_provider:
            raise ValidationException(f"该工具提供商名称{req.name.data}已存在")

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 创建自定义API工具提供商
            api_tool_provider = ApiToolProvider(
                account_id=account_id,
                name=req.name.data,
                icon=req.icon.data,
                description=openapi_schema.description,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data,
            )
            self.db.session.add(api_tool_provider)
            self.db.session.flush()

            # 创建自定义API工具并关联其提供商
            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    api_tool = ApiTool(
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters", []),
                    )
                    self.db.session.add(api_tool)

    def get_api_tool_provider(self, provider_id: UUID):
        """获取自定义API工具提供商信息"""

        # TODO: 实现授权认证模块后，完善账户相关逻辑
        account_id = "05a9c691-a5b0-4661-893a-430c760eb8cd"

        # 查询该工具的提供商
        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)

        # 检查是否为空且是否属于当前账户
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该自定义API工具提供商不存在")

        return api_tool_provider

    def get_api_tool(self, provider_id, tool_name):
        """获取自定义API工具信息"""

        # TODO: 实现授权认证模块后，完善账户相关逻辑
        account_id = "05a9c691-a5b0-4661-893a-430c760eb8cd"

        # 查询该工具
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()

        # 检查是否为空
        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException("该自定义API工具不存在")

        return api_tool

    def delete_api_tool_provider(self, provider_id: UUID):
        """删除自定义API工具提供商"""

        # TODO: 实现授权认证模块后，完善账户相关逻辑
        account_id = "05a9c691-a5b0-4661-893a-430c760eb8cd"

        # 查询该工具提供商
        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)

        # 检查是否为空且是否属于当前账户
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该自定义API工具提供商不存在")

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 删除该工具提供者的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id,
            ).delete()

            # 删除该工具提供者
            self.db.session.delete(api_tool_provider)
