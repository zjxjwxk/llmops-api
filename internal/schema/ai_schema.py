#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/11/7 20:10
@File   :   ai_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, UUID, Length


class OptimizePromptReq(FlaskForm):
    """优化Prompt请求"""

    prompt = StringField("prompt", validators=[
        DataRequired("Prompt不能为空"),
        Length(max=2000, message="Prompt长度不能超过2000个字符")
    ])


class GenerateSuggestedQuestionsReq(FlaskForm):
    """生成建议问题列表请求"""

    message_id = StringField("message_id", validators=[
        DataRequired("消息ID不能为空"),
        UUID(message="消息ID必须为UUID类型")
    ])
