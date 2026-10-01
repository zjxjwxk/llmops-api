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

from internal.model import App, Account
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AppService:
    """应用服务逻辑"""
    db: SQLAlchemy

    def create_app(self, account: Account) -> App:
        with self.db.auto_commit():
            # 1. 创建模型实体类
            app = App(name="新建应用", account_id=account.id, icon="", description="这是一个测试应用", )

            # 2. 将实体类添加到session中
            self.db.session.add(app)
        return app

    def get_app(self, id: uuid.UUID) -> App:
        app = self.db.session.query(App).get(id)
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
