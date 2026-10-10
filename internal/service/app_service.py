#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/25 21:16
@File   :   app_service.py
"""
import uuid
from dataclasses import dataclass

from injector import inject

from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.exception import NotFoundException, ForbiddenException
from internal.model import App, Account, AppConfigVersion
from internal.schema.app_schema import CreateAppReq
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""
    db: SQLAlchemy

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """创建应用"""

        with self.db.auto_commit():
            # 1. 创建应用记录
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 创建应用配置草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 更新应用草稿配置ID
            app.draft_app_config_id = app_config_version.id

        return app

    def get_app(self, app_id: uuid.UUID, account: Account) -> App:
        """获取应用信息"""

        # 获取应用信息
        app = self.get(App, app_id)

        # 判断应用是否存在
        if not app:
            raise NotFoundException("该应用不存在，请核实后重试")

        # 判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后重试")

        return app

    def update_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.db.session.query(App).get(id)
            app.name = "更新后应用"
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.db.session.query(App).get(id)
            self.db.session.delete(app)
        return app
