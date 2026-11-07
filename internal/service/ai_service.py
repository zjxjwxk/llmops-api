#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/11/7 20:26
@File   :   ai_service.py
"""
import json
from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.ai_entity import OPTIMIZE_PROMPT_TEMPLATE
from internal.exception import ForbiddenException
from internal.model import Account, Message
from internal.service.base_service import BaseService
from internal.service.conversation_service import ConversationService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AIService(BaseService):
    """AI辅助服务"""

    db: SQLAlchemy
    conversation_service: ConversationService

    @classmethod
    def optimize_prompt(cls, prompt: str) -> Generator[str, None, None]:
        """优化Prompt"""

        # 构建优化Prompt提示词模版
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "{prompt}")
        ])

        # 构建LLM
        llm = ChatOpenAI(temperature=0.5)

        # 构建链
        optimize_chain = prompt_template | llm | StrOutputParser()

        # 调用链并流式返回
        for optimize_prompt in optimize_chain.stream({"prompt": prompt}):
            data = {
                "optimize_prompt": optimize_prompt,
            }
            yield f"event: optimize_prompt\ndata: {json.dumps(data)}\n\n"

    def generate_suggested_questions(self, message_id: UUID, account: Account):
        """生成建议问题列表"""

        # 查询消息并校验权限
        message = self.get(Message, message_id)
        if not message or message.created_by != account.id:
            raise ForbiddenException("该消息不存在或无权访问")

        # 构建最新历史对话
        histories = f"Human: {message.query}\nAI: {message.answer}"

        # 调用服务生成建议问题
        return self.conversation_service.generate_suggested_questions(histories)
