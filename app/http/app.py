#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 19:29
@File   :   app.py
"""
import dotenv
from flask_login import LoginManager
from flask_migrate import Migrate

from app.http.module import injector
from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy

# 将.env文件加载到环境变量中
dotenv.load_dotenv()

# 应用配置
config = Config()

app = Http(
    __name__,
    config=config,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router)
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=True)
