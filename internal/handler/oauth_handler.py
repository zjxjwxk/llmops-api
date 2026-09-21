#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/9/20 17:08
@File   :   oauth_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service.oauth_service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    """第三方认证授权处理器"""

    oauth_service: OAuthService

    def provider(self, provider_name: str):
        """获取提供商认证授权重定向地址"""

        # 获取服务商OAuth类
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)

        # 获取服务商认证授权重定向地址
        redirect_url = oauth.get_authorization_url()

        return success_json({"redirect_url": redirect_url})

    def authorize(self, provider_name: str):
        """获取第三方OAuth信息"""

        # 提取请求并校验
        req = AuthorizeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务OAuth登录账号
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        return success_json(AuthorizeResp().dump(credential))
