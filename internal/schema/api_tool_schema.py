#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具OpenAPI Schema校验

@Author :   Xinkang Wu
@Time   :   2026/6/28 15:54
@File   :   api_tool_schema.py
"""

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError

from internal.model import ApiToolProvider
from internal.schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """OpenAPI Schema字符串校验请求"""

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])


class CreateApiToolReq(FlaskForm):
    """创建自定义API工具请求"""

    name = StringField("name", validators=[
        DataRequired(message="提供商名称不能为空"),
        Length(min=1, max=30, message="提供商名称长度必须在1-30之间")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="提供商图标不能为空"),
        URL(message="提供商图标格式必须为URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
    headers = ListField("headers")

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers列表中的元素类型必须为字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers列表中的字典必须仅包含key/value两个属性")


class GetApiToolProviderResp(Schema):
    """获取自定义API提供商信息的响应"""

    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        resp = {
            **data.__dict__,
            "created_at": int(data.created_at.timestamp())
        }
        return resp
