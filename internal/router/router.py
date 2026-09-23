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

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler, UploadFileHandler, DatasetHandler, \
    DocumentHandler, SegmentHandler, OAuthHandler, AccountHandler


@inject
@dataclass
class Router:
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler
    document_handler: DocumentHandler
    segment_handler: SegmentHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler

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
        blue_print.add_url_rule("/app/<uuid:id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)

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
        blue_print.add_url_rule("/api-tools", methods=["POST"],
                                view_func=self.api_tool_handler.create_api_tool_provider)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>", view_func=self.api_tool_handler.get_api_tool_provider)
        blue_print.add_url_rule("/api-tools", view_func=self.api_tool_handler.get_api_tool_providers_with_page)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>", methods=["POST"],
                                view_func=self.api_tool_handler.update_api_tool_provider)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>/delete", methods=["POST"],
                                view_func=self.api_tool_handler.delete_api_tool_provider)
        blue_print.add_url_rule("/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
                                view_func=self.api_tool_handler.get_api_tool)

        # 文件上传模块
        blue_print.add_url_rule("/upload-files/file", methods=["POST"], view_func=self.upload_file_handler.upload_file)
        blue_print.add_url_rule("/upload-files/image", methods=["POST"],
                                view_func=self.upload_file_handler.upload_image)

        # 知识库模块
        blue_print.add_url_rule("/datasets", methods=["POST"], view_func=self.dataset_handler.create_dataset)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>", view_func=self.dataset_handler.get_dataset)
        blue_print.add_url_rule("/datasets", view_func=self.dataset_handler.get_dataset_with_page)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/queries",
                                view_func=self.dataset_handler.get_dataset_queries)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>", methods=["POST"],
                                view_func=self.dataset_handler.update_dataset)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/delete", methods=["POST"],
                                view_func=self.dataset_handler.delete_dataset)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/hit", methods=["POST"], view_func=self.dataset_handler.hit)
        blue_print.add_url_rule("/datasets/embeddings", view_func=self.dataset_handler.embeddings_query)

        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents", methods=["POST"],
                                view_func=self.document_handler.create_documents)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>",
                                view_func=self.document_handler.get_document)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents",
                                view_func=self.document_handler.get_documents_with_page)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/batch/<string:batch>",
                                view_func=self.document_handler.get_documents_status)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name", methods=["POST"],
                                view_func=self.document_handler.update_document_name)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled", methods=["POST"],
                                view_func=self.document_handler.update_document_enabled)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete", methods=["POST"],
                                view_func=self.document_handler.delete_document)

        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments", methods=["POST"],
                                view_func=self.segment_handler.create_segment)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                                view_func=self.segment_handler.get_segments_with_page)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                                view_func=self.segment_handler.get_segment)
        blue_print.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                                methods=["POST"], view_func=self.segment_handler.update_segment)
        blue_print.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled",
            methods=["POST"], view_func=self.segment_handler.update_segment_enabled)
        blue_print.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete",
            methods=["POST"], view_func=self.segment_handler.delete_segment)

        # OAuth模块
        blue_print.add_url_rule("/oauth/<string:provider_name>", view_func=self.oauth_handler.provider)
        blue_print.add_url_rule("/oauth/authorize/<string:provider_name>", methods=["POST"],
                                view_func=self.oauth_handler.authorize)

        # 账号模块
        blue_print.add_url_rule("/account", view_func=self.account_handler.get_current_user)
        blue_print.add_url_rule("/account/password", methods=["POST"], view_func=self.account_handler.update_password)
        blue_print.add_url_rule("/account/name", methods=["POST"], view_func=self.account_handler.update_name)
        blue_print.add_url_rule("/account/avatar", methods=["POST"], view_func=self.account_handler.update_avatar)

        # 注册蓝图
        app.register_blueprint(blue_print)
