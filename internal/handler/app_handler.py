#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/21 17:31
@File   :   app_handler.py
"""
import json
import uuid
from dataclasses import dataclass
from operator import itemgetter
from typing import Dict, Any, Generator
from uuid import UUID

from flask_login import login_required, current_user
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
from redis import Redis

from internal.core.agent.agents import FunctionCallAgent
from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.conversation_entity import InvokeFrom
from internal.schema.app_schema import CompletionReq
from internal.service import AppService, ApiToolService, ConversationService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    appService: AppService
    vector_database_service: VectorDatabaseService
    api_tool_service: ApiToolService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService
    redis_client: Redis

    @login_required
    def create_app(self):
        """创建应用"""
        app = self.appService.create_app(current_user)
        return success_message(f"应用创建成功，id={app.id}")

    @login_required
    def get_app(self, id: UUID):
        """查询应用"""
        app = self.appService.get_app(id)
        return success_message(f"应用获取成功，name={app.name}")

    @login_required
    def update_app(self, id: UUID):
        """更新应用"""
        app = self.appService.update_app(id)
        return success_message(f"应用更新成功，name={app.name}")

    @login_required
    def delete_app(self, id: UUID):
        """删除应用"""
        app = self.appService.delete_app(id)
        return success_message(f"应用删除成功，id={app.id}")

    @login_required
    def debug(self, app_id: UUID):
        """应用会话调试接口，流式事件输出"""

        # 提取请求并校验
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 定义工具列表
        tools = [
            self.builtin_provider_manager.get_tool("google", "google_serper")(),
            self.builtin_provider_manager.get_tool("amap", "amap_weather")(),
            self.builtin_provider_manager.get_tool("wikipedia", "wikipedia_search")(),
        ]

        # 构建工具调用Agent
        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(),
                enable_long_term_memory=True,
                tools=tools
            ),
            AgentQueueManager(
                user_id=uuid.uuid4(),
                task_id=uuid.uuid4(),
                invoke_from=InvokeFrom.DEBUGGER,
                redis_client=self.redis_client
            )
        )

        def stream_event_response() -> Generator:
            """流式事件输出响应"""

            for agent_queue_event in agent.run(req.query.data, [], "用户介绍自己叫Xinkang"):
                data = {
                    "id": str(agent_queue_event.id),
                    "task_id": str(agent_queue_event.task_id),
                    "event": agent_queue_event.event,
                    "thought": agent_queue_event.thought,
                    "observation": agent_queue_event.observation,
                    "tool": agent_queue_event.tool,
                    "tool_input": agent_queue_event.tool_input,
                    "answer": agent_queue_event.answer,
                    "latency": agent_queue_event.latency
                }
                yield f"event: {agent_queue_event.event}\ndata: {json.dumps(data)}\n\n"

        return compact_generate_response(stream_event_response())

    def _debug(self, app_id: UUID):
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
        # 测试延迟任务

        # demo_task.delay(uuid.uuid4())
        # return self.api_tool_service.api_tool_invoke()

        # 测试总结历史消息

        # human_message = "你好，我叫Xinkang，你是？"
        # ai_message = "你好，我是大语言模型，有什么可以帮到你的？"
        # old_summary = "人类要求介绍 LLM 和 Agent 的概念。AI 解释称，LLM 是类似于“超级大脑”的大语言模型，擅长推理和生成但无法直接行动；而 Agent 则是基于 LLM 并配备了工具和记忆的智能体，如同“拥有手脚的实习生”，能够自主规划并执行任务，两者结合实现了从“思考”到“行动”的闭环。"
        # summary = self.conversation_service.summary(human_message, ai_message, old_summary)
        # return success_json({"summary": summary})

        # 测试生成会话名称

        # human_message = "介绍一下LLM和Agent的区别？"
        # conversation_name = self.conversation_service.generate_conversation_name(human_message)
        # return success_json({"conversation_name": conversation_name})

        # 测试生成建议问题

        # human_message = "介绍一下什么是LLM？LLM是大语言模型的简称。"
        # questions = self.conversation_service.generate_suggested_questions(human_message)
        # return success_json({"questions": questions})

        return success_message()

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
