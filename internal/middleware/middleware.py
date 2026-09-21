#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/20 11:28
@File   :   middleware.py
"""
from dataclasses import dataclass
from typing import Optional

from flask import Request
from injector import inject

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import JwtService, AccountService


@inject
@dataclass
class Middleware:
    """应用中间件"""

    jwt_service: JwtService
    account_service: AccountService

    def request_loader(self, request: Request) -> Optional[Account]:
        """请求加载器"""

        # 为llmops蓝图创建请求加载器
        if request.blueprint == "llmops":
            # 检查Authorization头部
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise UnauthorizedException("请登录后重试")

            # 检查空格
            if " " not in auth_header:
                raise UnauthorizedException("请登录后重试")

            # 分割Authorization头部，检查Bearer前缀
            auth_schema, access_token = auth_header.split(None, 1)
            if auth_schema.lower() != "bearer":
                raise UnauthorizedException("请登录后重试")

            # 解析JWT，获取账号
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")

            # 获取并返回账号信息
            return self.account_service.get_account(account_id)
        else:
            return None
