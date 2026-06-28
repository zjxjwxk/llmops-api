#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具OpenAPI Schema校验

@Author :   Xinkang Wu
@Time   :   2026/6/28 15:54
@File   :   api_tool_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI Schema字符串"""

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
