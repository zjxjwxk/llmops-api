#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/20 17:10
@File   :   oauth_service.py
"""
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from flask import request
from injector import inject

from internal.exception import NotFoundException
from pkg.oauth import OAuth, GithubOAuth
from pkg.sqlalchemy import SQLAlchemy
from . import JwtService
from .account_service import AccountService
from .base_service import BaseService
from ..model import AccountOAuth


@inject
@dataclass
class OAuthService(BaseService):
    """第三方OAuth服务"""

    db: SQLAlchemy
    jwt_service: JwtService
    account_service: AccountService

    @classmethod
    def get_all_oauth(cls) -> dict[str, OAuth]:
        """获取所有第三方OAuth方式"""

        github = GithubOAuth(
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            redirect_uri=os.getenv("GITHUB_REDIRECT_URI")
        )

        return {
            "github": github
        }

    @classmethod
    def get_oauth_by_provider_name(cls, provider_name: str) -> OAuth:
        """获取服务商对应的OAuth实现类"""

        all_oauth = cls.get_all_oauth()
        oauth = all_oauth.get(provider_name)

        if oauth is None:
            raise NotFoundException(f"该授权认证方式不存在：{provider_name}")

        return oauth

    def oauth_login(self, provider_name: str, code: str) -> dict[str, Any]:
        """第三方OAuth登录"""

        # 获取服务商OAuth
        oauth = self.get_oauth_by_provider_name(provider_name)

        # 请求获取OAuth Access Token
        oauth_access_token = oauth.get_access_token(code)

        # 请求获取第三方OAuth用户信息
        oauth_user_info = oauth.get_user_info(oauth_access_token)

        # 获取账号OAuth信息，根据OAuth用户信息中的OpenID查询账号
        account_oauth = self.account_service.get_account_oauth_by_provider_name_and_openid(provider_name,
                                                                                           oauth_user_info.id)

        if not account_oauth:
            # 用户初次通过该第三方OAuth服务商登陆，根据OAuth用户信息中的邮箱查询账号
            account = self.account_service.get_account_by_email(oauth_user_info.email)

            if not account:
                # 该邮箱未注册任何用户，则注册用户
                account = self.account_service.create_account(
                    name=oauth_user_info.name,
                    email=oauth_user_info.email,
                )

            # 创建账号OAuth信息
            account_oauth = self.create(
                AccountOAuth,
                account_id=account.id,
                provider=provider_name,
                openid=oauth_user_info.id,
                encrypted_token=oauth_access_token
            )
        else:
            # 查询账号信息
            account = self.account_service.get_account(account_oauth.account_id)

        # 更新账号信息
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        # 更新账号OAuth信息
        self.update(
            account_oauth,
            encrypted_token=oauth_access_token,
        )

        # 生成Access Token
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "LLMOps",
            "exp": expire_at
        }
        access_token = self.jwt_service.generate_token(payload)

        return {
            "expire_at": expire_at,
            "access_token": access_token
        }
