#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OAuth

@Author :   Xinkang Wu
@Time   :   2026/9/20 15:32
@File   :   oauth.py
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """OAuth用户信息类"""

    id: str
    name: str
    email: str


@dataclass
class OAuth(ABC):
    """第三方OAuth认证授权基类"""

    client_id: str  # 客户端ID
    client_secret: str  # 客户端密钥
    redirect_uri: str  # 重定向URI

    @abstractmethod
    def get_provider(self) -> str:
        """获取服务商名称"""

        pass

    @abstractmethod
    def get_authorization_url(self) -> str:
        """获取认证授权URL地址"""

        pass

    @abstractmethod
    def get_access_token(self, code: str) -> str:
        """获取访问令牌"""

        pass

    @abstractmethod
    def get_raw_user_info(self, token: str) -> dict:
        """获取OAuth原始信息"""

        pass

    def get_user_info(self, token: str) -> OAuthUserInfo:
        """获取OAuth用户信息"""

        # 获取OAuth原始信息
        raw_info = self.get_raw_user_info(token)
        return self._transform_user_info(raw_info)

    @abstractmethod
    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        """OAuth原始信息转换为OAuth用户信息"""

        pass
