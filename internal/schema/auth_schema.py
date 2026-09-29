#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/29 22:08
@File   :   auth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Email, Length, regexp

from pkg.password.password import password_pattern


class PasswordLoginReq(FlaskForm):
    """账号密码登录请求"""

    email = StringField("email", validators=[
        DataRequired("登录邮箱不能为空"),
        Email("登录邮箱格式错误"),
        Length(min=5, max=254, message="登录邮箱长度必须在5-254个字符")
    ])
    password = StringField("password", validators=[
        DataRequired("登录密码不能为空"),
        regexp(regex=password_pattern, message="登录密码至少包含一个字母、一个数字，长度必须在8-16位之间")
    ])


class PasswordLoginResp(Schema):
    """账号密码认证授权响应"""

    access_token = fields.String()
    expire_at = fields.Integer()
