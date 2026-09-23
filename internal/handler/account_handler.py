#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/22 21:43
@File   :   account_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.account_schema import GetCurrentUserResp, UpdatePasswordReq, UpdateNameReq, UpdateAvatarReq
from internal.service import AccountService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class AccountHandler:
    """账号处理器"""

    accoount_service: AccountService

    @login_required
    def get_current_user(self):
        """获取当前账号信息"""

        resp = GetCurrentUserResp()
        return success_json(resp.dump(current_user))

    @login_required
    def update_password(self):
        """更新当前账号密码"""

        # 提取请求并校验
        req = UpdatePasswordReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新密码
        self.accoount_service.update_password(req.password.data, current_user)

        return success_message("更新账号密码成功")

    @login_required
    def update_name(self):
        """更新当前账号名称"""

        # 提取请求并校验
        req = UpdateNameReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新账号名称
        self.accoount_service.update_account(current_user, name=req.name.data)

        return success_message("更新账号名称成功")

    @login_required
    def update_avatar(self):
        """更新当前账号头像"""

        # 提取请求并校验
        req = UpdateAvatarReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新账号头像
        self.accoount_service.update_account(current_user, avatar=req.avatar.data)

        return success_message("更新账号头像成功")
