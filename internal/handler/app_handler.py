#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:31
@File   :   app_handler.py
"""
from dataclasses import dataclass
from operator import itemgetter
from typing import Dict, Any
from uuid import UUID

from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI

from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    appService: AppService
    vector_database_service: VectorDatabaseService

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
            ("system", "你是一个强大的聊天机器人，能根据对应的上下文和历史对话信息进行相应的回复。\n\n"
                       "<context>{context}</context>"),
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
        retriever = (self.vector_database_service.get_retriever()
                     | RunnableLambda(self.vector_database_service.combine_documents))
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | RunnableLambda(itemgetter("history")),
            context=RunnableLambda(itemgetter("query")) | retriever
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_context)  # type: ignore[arg-type]

        # 调用链
        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config=RunnableConfig(configurable={"memory": memory}))

        return success_json({"content": content})

    def ping(self):
        return {"ping": "pong"}

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """记载记忆变量"""

        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储上下文信息到记忆中"""

        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    @classmethod
    def _combine_documents(cls, documents: list[Document]) -> str:
        """将文档列表使用换行符进行合并"""
        return "\n\n".join([document.page_content for document in documents])
