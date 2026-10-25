#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/8/28 21:47
@File   :   function_call_agent.py
"""
import json
import logging
import re
import time
import uuid
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage, ToolMessage, \
    messages_to_dict, AIMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from internal.core.agent.agents.base_agent import BaseAgent
from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE, \
    DATASET_RETRIEVAL_TOOL_NAME, MAX_ITERATION_RESPONSE
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.exception import FailException


class FunctionCallAgent(BaseAgent):
    """基于函数/工具调用的Agent"""

    def _build_agent(self) -> CompiledStateGraph:

        # 创建图
        graph = StateGraph(AgentState)

        # 添加节点
        graph.add_node("preset_operation", self._preset_operation_node)
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 添加边、起点和终点
        graph.set_entry_point("preset_operation")
        graph.add_conditional_edges("preset_operation", self._preset_operation_condition)
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 编译图并返回
        agent = graph.compile()
        return agent

    def _preset_operation_node(self, state: AgentState) -> AgentState:
        """预设操作：输入审核、数据预处理、条件边等"""

        review_config = self.agent_config.review_config
        query = state["messages"][-1].content

        # 输入审核
        if review_config["enable"] and review_config["inputs_config"]["enable"]:
            contains_keyword = any(keyword.lower() in query.lower() for keyword in review_config["keywords"])
            # 若监测到敏感词，直接输出预设回复
            if contains_keyword:
                preset_response = review_config["inputs_config"]["preset_response"]
                # 流式输出预设消息事件
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=preset_response,
                    message=messages_to_dict(state["messages"]),
                    answer=preset_response,
                    latency=0,
                ))
                # 流式输出结束事件
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ))
                return {"messages": [AIMessage(preset_response)]}

        return {"messages": []}

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """长期记忆召回节点"""

        # 获取长期记忆
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            # 流式输出长期记忆事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory
            ))

        # 构建预设消息列表
        preset_messages = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory
            ))
        ]

        # 获取短期记忆
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 校验是否为消息对（偶数）
            if len(history) % 2 != 0:
                # 流式输出错误事件
                self.agent_queue_manager.publish_error(state["task_id"], "智能体历史消息列表格式错误")
                logging.exception(
                    f"智能体历史消息列表格式错误，len(history)={len(history)}，history={json.dumps(messages_to_dict(history))}")
                raise FailException("智能体历史消息列表格式错误")
            # 添加短期记忆
            preset_messages.extend(history)

        # 添加人类消息
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 将State中的人类消息替换为预设消息+人类消息
        return {"messages": [RemoveMessage(id=human_message.id), *preset_messages]}

    def _llm_node(self, state: AgentState) -> AgentState:
        """LLM节点"""

        # 检查智能体迭代次数
        if state["iteration_count"] > self.agent_config.max_iteration_count:
            # 流式输出预设消息事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_MESSAGE,
                thought=MAX_ITERATION_RESPONSE,
                message=messages_to_dict(state["messages"]),
                answer=MAX_ITERATION_RESPONSE,
                latency=0,
            ))
            # 流式输出结束事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))
            return {"messages": [AIMessage(MAX_ITERATION_RESPONSE)]}

        # 初始化事件参数
        id = uuid.uuid4()
        start_at = time.perf_counter()

        # 获取LLM
        llm = self.agent_config.llm

        # 检测是否支持/需要绑定工具
        if hasattr(llm, "bind_tools") and callable(getattr(llm, "bind_tools")) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)

        gathered = None  # 合并Chunk
        is_first_chunk = True  # 是否为第一个Chunk
        generation_type = ""  # 生成类型
        tool_called = False

        try:
            # 流式调用LLM
            for chunk in llm.stream(state["messages"]):
                if is_first_chunk:
                    gathered = chunk
                    is_first_chunk = False
                else:
                    gathered += chunk

                # 判断生成类型（工具调用->推理，消息内容->消息）
                if chunk.tool_calls:
                    generation_type = "thought"
                    tool_called = True
                elif chunk.content:
                    generation_type = "message"

                # 若为消息类型，且消息内容不为空，则为Chunk添加消息事件
                if generation_type == "message" and chunk.content:
                    # 输出审核
                    review_config = self.agent_config.review_config
                    content = chunk.content
                    if review_config["enable"] and review_config["outputs_config"]["enable"]:
                        for keyword in review_config["keywords"]:
                            content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)

                    # 流式输出消息事件
                    self.agent_queue_manager.publish(state["task_id"], AgentThought(
                        id=id,
                        task_id=state["task_id"],
                        event=QueueEvent.AGENT_MESSAGE,
                        thought=content,
                        message=messages_to_dict(state["messages"]),
                        answer=content,
                        latency=time.perf_counter() - start_at,
                    ))
        except Exception as e:
            logging.exception(f"LLM节点执行错误，错误信息：{str(e)}")
            # 流式输出错误事件
            self.agent_queue_manager.publish_error(state["task_id"], f"LLM节点执行错误，错误信息：{str(e)}")
            raise e

        # 若有工具调用，则添加推理事件
        if tool_called:
            # 流式输出推理事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_THOUGHT,
                thought=json.dumps(gathered.tool_calls),
                message=messages_to_dict(state["messages"]),
                latency=time.perf_counter() - start_at,
            ))
        else:
            # 若无工具调用，则表示为最终回答，流式输出停止事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))

        return {"messages": [gathered], "iteration_count": state["iteration_count"] + 1}

    def _tools_node(self, state: AgentState) -> AgentState:
        """工具执行节点"""

        # 构建工具字典
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        # 获取AI消息中的工具调用参数
        tool_calls = state["messages"][-1].tool_calls

        messages = []
        for tool_call in tool_calls:
            # 初始化事件参数
            id = uuid.uuid4()
            start_at = time.perf_counter()

            try:
                # 获取工具并调用
                tool = tools_by_name[tool_call["name"]]
                tool_result = tool.invoke(tool_call["args"])
            except Exception as e:
                # 添加工具错误信息
                tool_result = f"工具{tool_call['name']}执行错误：{str(e)}"

            # 添加工具消息
            messages.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(tool_result),
                name=tool_call["name"],
            ))

            # 判断事件类型（工具名称 => 知识库检索 ｜ Agent动作）
            if tool_call["name"] == DATASET_RETRIEVAL_TOOL_NAME:
                event = QueueEvent.DATASET_RETRIEVAL
            else:
                event = QueueEvent.AGENT_ACTION

            # 流式输出（知识库检索/动作）事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=event,
                observation=json.dumps(tool_result),
                tool=tool_call["name"],
                tool_input=tool_call["args"],
                latency=time.perf_counter() - start_at,
            ))

        return {"messages": messages}

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        """工具调用条件边：判断是需要工具调用，还是直接结束"""

        # 提取最后一条消息
        message = state["messages"][-1]

        # 判断是否需要工具调用
        if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
            return "tools"

        return END

    @classmethod
    def _preset_operation_condition(cls, state: AgentState) -> Literal["long_term_memory_recall", "__end__",]:
        """预设操作条件边：判断是否直接返回预设响应"""

        # 提取最后一条消息
        message = state["messages"][-1]

        # 判断是否直接返回预设响应
        if message.type == "ai":
            return END

        return "long_term_memory_recall"
