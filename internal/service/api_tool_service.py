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
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.exception import ValidationException, NotFoundException
from internal.model import ApiToolProvider, ApiTool, Account
from internal.schema.api_tool_schema import CreateApiToolReq, GetApiToolProvidersWithPageReq, UpdateApiToolProviderReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API工具服务"""

    db: SQLAlchemy
    api_provider_manager: ApiProviderManager

    def create_api_tool_provider(self, req: CreateApiToolReq, account: Account) -> None:
        """创建自定义API工具提供商"""

        # 检验并提取openapi_schema
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 判断该工具提供商名称是否已存在于当前账户
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account.id,
            name=req.name.data,
        ).one_or_none()

        if api_tool_provider:
            raise ValidationException(f"该工具提供商名称{req.name.data}已存在")

        # 创建自定义API工具提供商
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )

        # 创建自定义API工具并关联其提供商
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def get_api_tool_provider(self, provider_id: UUID, account: Account):
        """获取自定义API工具提供商"""

        # 查询该工具的提供商
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 检查是否为空且是否属于当前账户
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该自定义API工具提供商不存在")

        return api_tool_provider

    def get_api_tool_providers_with_page(self, req: GetApiToolProvidersWithPageReq, account: Account) -> tuple[
        list[Any], Paginator]:
        """获取自定义API工具提供商分页"""

        # 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [ApiToolProvider.account_id == account.id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))

        # 分页查询数据
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    def update_api_tool_provider(self, provider_id: UUID, req: UpdateApiToolProviderReq, account: Account):
        """更新自定义API工具提供商"""

        # 查询该工具提供者
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 检查是否为空且是否属于当前账户
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该自定义API工具提供商不存在")

        # 检验并提取openapi_schema
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 判断更新后的工具提供商名称是否已存在于当前账户（不包括当前请求的provider_id）
        exist_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account.id,
            ApiToolProvider.name == req.name.data,
            ApiToolProvider.id != api_tool_provider.id
        ).one_or_none()

        if exist_api_tool_provider:
            raise ValidationException(f"该工具提供商名称{req.name.data}已存在")

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 先删除该工具提供者的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account.id,
            ).delete()

        # 更新该工具提供者的信息
        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data
        )

        # 创建更新后的自定义API工具并关联其提供商
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def delete_api_tool_provider(self, provider_id: UUID, account: Account):
        """删除自定义API工具提供商"""

        # 查询该工具提供商
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 检查是否为空且是否属于当前账户
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该自定义API工具提供商不存在")

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 删除该工具提供者的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account.id,
            ).delete()

            # 删除该工具提供者
            self.db.session.delete(api_tool_provider)

    def get_api_tool(self, provider_id, tool_name, account: Account):
        """获取自定义API工具"""

        # 查询该工具
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()

        # 检查是否为空
        if api_tool is None or api_tool.account_id != account.id:
            raise NotFoundException("该自定义API工具不存在")

        return api_tool

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
