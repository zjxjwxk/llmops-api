#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JWT服务

@Author :   Xinkang Wu
@Time   :   2026/9/19 17:04
@File   :   jwt_service.py
"""
import os
from dataclasses import dataclass
from typing import Any

import jwt
from injector import inject


@inject
@dataclass
class JwtService:
    """JWT服务"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        """生成JWT"""

        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        """解析JWT"""

        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("用户凭证已过期，请重新登录")
        except jwt.InvalidTokenError:
            raise ValueError("无效的用户凭证，请重新登录")
        except Exception as e:
            raise e
