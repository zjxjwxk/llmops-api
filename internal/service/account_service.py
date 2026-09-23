#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
账号服务

@Author :   Xinkang Wu
@Time   :   2026/9/20 15:06
@File   :   account_service.py
"""
import base64
import secrets
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import Account, AccountOAuth
from pkg.password import hash_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AccountService(BaseService):
    """账号服务"""

    db: SQLAlchemy

    def get_account(self, account_id: UUID) -> Account:
        """获取账号信息（根据账号UUID）"""

        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(self, provider_name: str, openid: str) -> AccountOAuth:
        """获取账户OAuth信息"""

        return self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid
        ).one_or_none()

    def get_account_by_email(self, email: str) -> Account:
        """查询账号信息（根据邮箱）"""

        return self.db.session.query(Account).filter(
            Account.email == email
        ).one_or_none()

    def create_account(self, **kwargs) -> Account:
        """创建账号"""

        return self.create(Account, **kwargs)

    def update_password(self, password: str, account: Account) -> Account:
        """更新当前账号密码"""

        # 生成密码随机盐值
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # 对密码+盐值进行加密
        password_hashed = hash_password(password, salt)

        # 对加密密码进行Base64编码
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        # 更新账号密码和盐值
        self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)
        return account

    def update_account(self, account: Account, **kwargs):
        """更新账号信息"""

        self.update(account, **kwargs)
        return account
