#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/28 22:53
@File   :   auth_handler.py
"""
from dataclasses import dataclass

from flask_login import logout_user, login_required
from injector import inject

from internal.schema.auth_schema import PasswordLoginReq, PasswordLoginResp
from internal.service import AccountService
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AuthHandler:
    """认证授权处理器"""

    account_service: AccountService

    def password_login(self):
        """账号密码登录"""

        # 提取请求并校验
        req = PasswordLoginReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务登录账号
        credential = self.account_service.password_login(req.email.data, req.password.data)

        resp = PasswordLoginResp()
        return success_json(resp.dump(credential))

    @login_required
    def logout(self):
        """退出登录"""

        logout_user()
        return success_message("退出登录成功")
