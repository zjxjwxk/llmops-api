#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:31
@File   :   app_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.exception import NotFoundException
from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class AppHandler:
    """应用控制器"""
    appService: AppService

    def create_app(self):
        """创建应用"""
        app = self.appService.create_app()
        return success_message(f"应用创建成功，id={app.id}")

    def get_app(self, id: UUID):
        """查询应用"""
        app = self.appService.get_app(id)
        return success_message(f"应用获取成功，name={app.name}")

    def update_app(self, id: UUID):
        """更新应用"""
        app = self.appService.update_app(id)
        return success_message(f"应用更新成功，name={app.name}")

    def delete_app(self, id: UUID):
        """删除应用"""
        app = self.appService.delete_app(id)
        return success_message(f"应用删除成功，id={app.id}")

    def debug(self, app_id: UUID):
        """聊天接口"""

        # 1. 从POST请求中获取输入并校验
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2. 构建PromptTemplate, ChatModel, OutputParser组件
        prompt = ChatPromptTemplate.from_template("{query}")
        llm = ChatOpenAI(model="kimi-k2-0905-preview")
        parser = StrOutputParser()

        # 3. 构建链
        chain = prompt | llm | parser

        # 4. 调用链
        content = chain.invoke({"query": req.query.data})

        return success_json({"content": content})

    def ping(self):
        raise NotFoundException("Pong not found")
        # return {"ping": "pong"}
