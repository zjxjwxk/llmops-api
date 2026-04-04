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
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
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

        # 从POST请求中获取输入并校验
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 创建Prompt
        prompt = ChatPromptTemplate([
            ("system", "你是一个强大的聊天机器人，能根据用户的提问进行相应的回复"),
            MessagesPlaceholder("history"),
            ("human", "{query}")
        ])

        # 创建Memory
        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt")
        )

        # 创建LLM
        llm = ChatOpenAI()

        # 创建Chain
        chain = RunnablePassthrough.assign(
            history=RunnableLambda(lambda x: memory.load_memory_variables({}).get("history"))
        ) | prompt | llm | StrOutputParser()

        # 调用链
        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input)

        memory.save_context(chain_input, {"output": content})

        return success_json({"content": content})

    def ping(self):
        raise NotFoundException("Pong not found")
        # return {"ping": "pong"}
