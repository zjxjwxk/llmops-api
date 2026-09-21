#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub OAuth

@Author :   Xinkang Wu
@Time   :   2026/9/20 15:45
@File   :   github_oauth.py
"""
import urllib.parse

import requests

from pkg.oauth.oauth import OAuth, OAuthUserInfo


class GithubOAuth(OAuth):
    """GitHub OAuth第三方认证授权类"""

    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"  # 认证授权接口
    _ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # 获取访问令牌接口
    _USER_INFO_URL = "https://api.github.com/user"  # 获取用户信息接口
    _EMAIL_INFO_URL = "https://api.github.com/user/emails"  # 获取用户邮箱接口

    def get_provider(self) -> str:
        return "github"

    def get_authorization_url(self) -> str:

        # 组装URL参数
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 仅请求用户基本信息
        }
        return f"{self._AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str) -> str:

        # 组装请求数据
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        headers = {"Accept": "application/json"}

        # 发起POST请求
        resp = requests.post(self._ACCESS_TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        # 提取access_token
        access_token = resp_json.get("access_token")
        if not access_token:
            raise ValueError(f"GitHub OAuth授权失败：{resp_json}")

        return access_token

    def get_raw_user_info(self, token: str) -> dict:

        # 组装请求数据
        headers = {"Authorization": f"token {token}"}

        # 发起GET请求，获取用户信息
        user_info_resp = requests.get(self._USER_INFO_URL, headers=headers)
        user_info_resp.raise_for_status()
        raw_info = user_info_resp.json()

        # 发起GET请求，获取用户邮箱
        email_info_resp = requests.get(self._EMAIL_INFO_URL, headers=headers)
        email_info_resp.raise_for_status()
        email_info = email_info_resp.json()

        # 提取邮箱
        primary_email = next((email for email in email_info if email.get("primary", None)), None)

        return {**raw_info, "email": primary_email.get("email", None)}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:

        # 获取邮箱
        email = raw_info.get("email")
        if not email:
            email = f"{raw_info.get('id')}+{raw_info.get('login')}@user.no-reply@github.com"

        # 组装数据
        return OAuthUserInfo(
            id=str(raw_info.get("id")),
            name=str(raw_info.get("name")),
            email=str(email)
        )
