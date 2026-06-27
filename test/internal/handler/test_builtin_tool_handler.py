#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置工具处理器测试类

@Author :   Xinkang Wu
@Time   :   2026/6/27 14:18
@File   :   test_builtin_tool_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestBuiltinToolHandler:
    """内置工具处理器测试类"""

    def test_get_categories(self, client):
        """测试获取所有分类信息"""
        response = client.get("/builtin-tools/categories")
        assert response.status_code == 200
        assert response.json.get("code") == HttpCode.SUCCESS
        assert len(response.json.get("data")) > 0

    def test_get_builtin_tools(self, client):
        """测试获取所有内置工具信息"""
        response = client.get("/builtin-tools")
        assert response.status_code == 200
        assert response.json.get("code") == HttpCode.SUCCESS
        assert len(response.json.get("data")) > 0

    @pytest.mark.parametrize(
        "provider_name, tool_name",
        [
            ("google", "google_serper"),
            ("invalid_provider", "invalid_tool"),
        ]
    )
    def test_get_provider_tool(self, provider_name, tool_name, client):
        """测试获取指定服务提供商的指定工具信息"""
        response = client.get(f"/builtin-tools/{provider_name}/tools/{tool_name}")
        assert response.status_code == 200
        if provider_name == "google":
            assert response.json.get("code") == HttpCode.SUCCESS
            assert response.json.get("data").get("name") == tool_name
        elif provider_name == "invalid_provider":
            assert response.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("provider_name", ["google", "invalid_provider"])
    def test_get_provider_icon(self, provider_name, client):
        """测试获取服务提供商icon"""
        response = client.get(f"/builtin-tools/{provider_name}/icon")
        assert response.status_code == 200
        if provider_name == "invalid_provider":
            assert response.json.get("code") == HttpCode.NOT_FOUND
