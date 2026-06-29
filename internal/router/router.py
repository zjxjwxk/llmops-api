#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:50
@File   :   router.py
"""
from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler


@inject
@dataclass
class Router:
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler

    def register_router(self, app: Flask):
        """注册路由"""

        # 创建蓝图
        blue_print = Blueprint("llmops", __name__, url_prefix="")

        # AI应用模块
        blue_print.add_url_rule("/ping", view_func=self.app_handler.ping)
        blue_print.add_url_rule("/apps/<uuid:app_id>/debug", methods=["POST"], view_func=self.app_handler.debug)
        blue_print.add_url_rule("/app", methods=["POST"], view_func=self.app_handler.create_app)
        blue_print.add_url_rule("/app/<uuid:id>", view_func=self.app_handler.get_app)
        blue_print.add_url_rule("/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app)
        blue_print.add_url_rule("/app/<uuid:id>", methods=["DELETE"], view_func=self.app_handler.delete_app)

        # 内置插件广场模块
        blue_print.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools)
        blue_print.add_url_rule("/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
                                view_func=self.builtin_tool_handler.get_provider_tool)
        blue_print.add_url_rule("/builtin-tools/<string:provider_name>/icon",
                                view_func=self.builtin_tool_handler.get_provider_icon)
        blue_print.add_url_rule("/builtin-tools/categories", view_func=self.builtin_tool_handler.get_categories)

        # 自定义API插件模块
        blue_print.add_url_rule("/api-tools/validate-openapi-schema", methods=["POST"],
                                view_func=self.api_tool_handler.validate_openapi_schema)
        blue_print.add_url_rule("/api-tools", methods=["POST"], view_func=self.api_tool_handler.create_api_tool)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>", methods=["DELETE"],
                                view_func=self.api_tool_handler.delete_api_tool_provider)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>", view_func=self.api_tool_handler.get_api_tool_provider)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
                                view_func=self.api_tool_handler.get_api_tool)

        # 注册蓝图
        app.register_blueprint(blue_print)
