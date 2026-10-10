#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:31
@File   :   app_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject

from internal.schema.app_schema import CreateAppReq, GetAppResp
from internal.service import AppService
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    appService: AppService

    @login_required
    def create_app(self):
        """创建应用"""

        # 提取请求并校验
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建应用
        app = self.appService.create_app(req, current_user)

        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: UUID):
        """获取应用信息"""

        # 调用服务获取应用信息
        app = self.appService.get_app(app_id, current_user)

        resp = GetAppResp()
        return success_json(resp.dump(app))

    def ping(self):
        return success_message()
