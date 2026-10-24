#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话常量

@Author :   Xinkang Wu
@Time   :   2026/8/23 23:07
@File   :   conversation_entity.py
"""
from enum import Enum

from pydantic import BaseModel, Field

# 摘要总结Prompt模版
SUMMARIZER_TEMPLATE = """逐步总结提供的对话内容，在之前的总结基础上继续添加并返回一个新的总结。

EXAMPLE
当前总结:
人类询问 AI 对人工智能的看法。AI 认为人工智能是一股向善的力量。

新的会话:
Human: 为什么你认为人工智能是一股向善的力量？
AI: 因为人工智能将帮助人类发挥他们全部的潜力。

新的总结:
人类询问 AI 对人工智能的看法，AI 认为人工智能是一股向善的力量，因为它将帮助人类发挥全部潜力。
END OF EXAMPLE

当前总结:
{summary}

新的会话:
{new_lines}

新的总结:"""

# 生成会话名称Prompt模版
CONVERSATION_NAME_TEMPLATE = "请根据用户对话提炼出主题"

# 生成建议问题Prompt模版
SUGGESTED_QUESTIONS_TEMPLATE = "请根据历史对话消息预测人类接下来可能会问的三个问题"


class ConversationInfo(BaseModel):
    """将用户输入分解为意图和主题，请确保输出语言和输入语言一致

    示例1：
    用户输入：Hi, my name is Xinkang.
    {
        "language_type": "用户的输入是纯英文",
        "reasoning": "输出语言必须是英文",
        "subject": "User greets me"
    }

    示例2：
    用户输入：介绍一下LLM是什么？
    {
        "language_type": "用户的输入是中英文混合",
        "reasoning": "英文部分是专有名词，主要意图还是用中文描述的，所以输出语言必须是中文",
        "subject": "询问LLM是什么"
    }

    示例3：
    用户输入：为什么Python的Performance比Java差？
    {
        "language_type": "用户的输入是中英文混合",
        "reasoning": "英文部分是专有名词和口语化输入，主要意图还是用中文描述的，所以输出语言必须是中文",
        "subject": "询问Python和Java的性能对比"
    }
    """

    language_type: str = Field(description="用户输入的语言类型")
    reasoning: str = Field(description="对用户输入的语言类型判断的推理过程")
    subject: str = Field(description="对用户输入进行简短总结，提取输入的意图和主题，输出语言必须和输入语言保持一致")


class SuggestedQuestions(BaseModel):
    """预测人类接下来可能会问的三个问题，每个问题保持在50个字符以内。
    生成的内容必须为字符串数组：["问题1", "问题2", "问题3"]"""

    questions: list[str] = Field(description="建议问题列表，类型为字符串数组")


class InvokeFrom(str, Enum):
    """调用来源"""

    SERVICE_API = "service_api"  # 开放API服务调用
    WEB_APP = "web_app"  # Web应用
    DEBUGGER = "debugger"  # 调试页面


class MessageStatus(str, Enum):
    """消息状态"""

    NORMAL = "normal"  # 正常
    STOP = "stop"  # 停止
    ERROR = "error"  # 出错
    REJECT = "reject"  # 拒绝
