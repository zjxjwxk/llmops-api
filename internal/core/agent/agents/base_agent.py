#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础Agent

@Author :   Xinkang Wu
@Time   :   2026/8/28 21:28
@File   :   base_agent.py
"""
import uuid
from abc import abstractmethod, ABC
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic import PrivateAttr

from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, AgentThought
from internal.exception import FailException


class BaseAgent(Serializable, Runnable, ABC):
    """基于Runnable的Agent基类"""

    llm: BaseLanguageModel  # LLM
    agent_config: AgentConfig  # Agent配置
    _agent: CompiledStateGraph = PrivateAttr(None)  # 编译后的图
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)  # Agent事件队列管理器

    class Config:
        # 允许接受任意类型字段（包括私有变量），且不需要校验器
        arbitrary_types_allowed = True

    def __init__(
            self,
            llm: BaseLanguageModel,
            agent_config: AgentConfig,
            *args,
            **kwargs,
    ):
        """构造函数"""

        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)

        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """构建Agent图节点"""

        raise NotImplementedError("_build_agent()未实现")

    def invoke(self, input: AgentState, config: Optional[RunnableConfig] = None,
               **kwargs: Optional[Any]) -> AgentResult:
        """非流式输出响应"""

        # TODO: 非流式输出响应，待开放API模块完成后实现
        pass

    def stream(
            self,
            input: AgentState,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any]
    ) -> Iterator[AgentThought]:
        """流式输出响应"""

        if not self._agent:
            raise FailException("智能体未成功构建，请核实后重试")

        # 初始化Agent状态
        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)

        # 创建并启动子线程
        thread = Thread(
            target=self._agent.invoke,
            args=(input,)
        )
        thread.start()

        # 监听智能体事件队列管理器中的该任务
        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """只读属性，获取智能体事件队列管理器"""
        return self._agent_queue_manager
