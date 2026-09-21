#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
账号服务

@Author :   Xinkang Wu
@Time   :   2026/9/20 15:06
@File   :   account_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import Account, AccountOAuth
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
