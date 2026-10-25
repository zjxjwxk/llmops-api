#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/8/29 16:22
@File   :   queue_entity.py
"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class QueueEvent(str, Enum):
    """队列事件枚举"""

    LONG_TERM_MEMORY_RECALL = "long_term_memory_recall"  # 长期记忆召回事件
    AGENT_THOUGHT = "agent_thought"  # 智能体推理事件
    AGENT_MESSAGE = "agent_message"  # 智能体消息事件
    AGENT_ACTION = "agent_action"  # 智能体动作事件
    DATASET_RETRIEVAL = "dataset_retrieval"  # 知识库检索事件
    AGENT_END = "agent_end"  # 智能体结束事件
    STOP = "stop"  # 智能体停止事件
    ERROR = "error"  # 智能体错误事件
    TIMEOUT = "timeout"  # 智能体超时事件
    PING = "ping"  # PING连通事件


class AgentThought(BaseModel):
    """智能体推理观察模型"""

    id: UUID  # 事件ID
    task_id: UUID  # 任务ID

    # 事件的推理和观察
    event: QueueEvent
    thought: str = ""  # LLM推理内容
    observation: str = ""  # 观察内容

    # 工具
    tool: str = ""  # 工具名称
    tool_input: dict = Field(default_factory=dict)  # 工具输入

    # 消息
    message: list[dict] = Field(default_factory=dict)  # 推理使用的消息列表
    message_token_count: int = 0  # 输入消息消耗的Token数
    message_unit_price: float = 0  # 输入Token单价
    message_price_unit: float = 0  # 输出Token价格单位

    # 回答
    answer: str = ""  # LLM生成的最终答案
    answer_token_count: int = 0  # 输出回答消耗Token数
    answer_unit_price: float = 0  # 输出Token单价
    answer_price_unit: float = 0  # 输出Token价格单位

    # Agent
    total_token_count: int = 0  # 总Token消耗数量
    total_price: float = 0  # Token花费总价
    latency: float = 0  # 步骤推理耗时


class AgentResult(BaseModel):
    """智能体推理观察最终结果"""

    # TODO: 智能体非流式输出响应，待开放API模块完成后实现
    pass
