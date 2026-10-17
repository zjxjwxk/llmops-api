#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:31
@File   :   app_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.app_schema import CreateAppReq, GetAppResp, GetPublishHistoriesWithPageReq, \
    GetPublishHistoriesWithPageResp
from internal.service import AppService
from pkg.paginator import PageModel
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService

    @login_required
    def create_app(self):
        """创建应用"""

        # 提取请求并校验
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建应用
        app = self.app_service.create_app(req, current_user)

        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: UUID):
        """获取应用信息"""

        # 调用服务获取应用信息
        app = self.app_service.get_app(app_id, current_user)

        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def get_draft_app_config(self, app_id: UUID):
        """获取应用草稿配置"""

        # 调用服务获取应用草稿配置
        draft_config = self.app_service.get_draft_app_config(app_id, current_user)

        return success_json(draft_config)

    @login_required
    def get_publish_histories_with_page(self, app_id: UUID):
        """获取应用发布历史列表分页"""

        # 提取请求并校验
        req = GetPublishHistoriesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务获取应用发布历史列表分页
        app_config_versions, paginator = self.app_service.get_publish_histories_with_page(app_id, req, current_user)

        # 构建分页响应
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(app_config_versions), paginator=paginator))

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """更新应用草稿配置"""

        # 提取请求
        draft_app_config = request.get_json(force=True, silent=True) or {}

        # 调用服务更新应用草稿配置
        self.app_service.update_draft_app_config(app_id, draft_app_config, current_user)

        return success_message("更新应用草稿配置成功")

    @login_required
    def publish(self, app_id: UUID):
        """发布应用配置"""

        self.app_service.publish_draft_app_config(app_id, current_user)

        return success_message("发布应用配置成功")

    @login_required
    def cancel_publish(self, app_id: UUID):
        """取消发布应用配置"""

        self.app_service.cancel_publish_app_config(app_id, current_user)

        return success_message("取消发布应用配置成功")

    def ping(self):
        return success_message()
