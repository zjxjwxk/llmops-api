#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/19 17:48
@File   :   password.py
"""
import base64
import binascii
import hashlib
import re
from typing import Any

# 密码校验正则表达式，至少包含一个字母、一个数字，长度在8-16之间
password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,16}$"


def validate_password(password: str, pattern: str = password_pattern):
    """验证密码是否符合要求"""
    if re.match(pattern, password) is None:
        raise ValueError("密码必须包含至少一个字母、一个数字，长度在8-16之间")
    return


def hash_password(password: str, salt: Any) -> bytes:
    """对密码+盐进行哈希处理"""

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return binascii.hexlify(dk)


def compare_password(password: str, password_hash_base64: Any, salt_base64: Any) -> bool:
    """校验密码是否匹配"""

    return hash_password(password, base64.b64decode(salt_base64)) == base64.b64decode(password_hash_base64)
