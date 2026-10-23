#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/8/27 21:18
@File   :   token_buffer_memory.py
"""
from dataclasses import dataclass

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.entity.conversation_entity import MessageStatus
from internal.model.conversation import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy


@dataclass
class TokenBufferMemory:
    """基于Token长度的缓冲记忆"""

    db: SQLAlchemy
    conversation: Conversation
    model_instance: BaseLanguageModel

    def get_history_prompt_messages(self, max_token_limit: int = 2000, message_limit: int = 10) -> list[AnyMessage]:
        """获取历史消息列表"""

        if self.conversation is None:
            return []

        # 查询历史消息列表，按时间倒序，并且需为有效消息
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status == MessageStatus.NORMAL,
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        # 转换为LangChain Message
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                HumanMessage(content=message.query),
                AIMessage(content=message.answer),
            ])

        # 计算Token长度并截取多余消息
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
        )

    def get_history_prompt_text(
            self,
            human_prefix: str = "Human",
            ai_prefix: str = "AI",
            max_token_limit: int = 2000,
            message_limit: int = 10
    ) -> str:
        """获取历史消息文本（用于文本类型LLM）"""

        # 获取历史消息列表
        messages = self.get_history_prompt_messages(max_token_limit, message_limit)

        # 将消息列表转换为文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
