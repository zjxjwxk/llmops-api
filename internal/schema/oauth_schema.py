#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/20 17:32
@File   :   oauth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired


class AuthorizeReq(FlaskForm):
    """第三方认证授权请求"""

    code = StringField("code", validators=[DataRequired("code不能为空")])


class AuthorizeResp(Schema):
    """第三方认证授权响应"""

    access_token = fields.String()
    expire_at = fields.Integer()
   