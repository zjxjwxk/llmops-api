#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/24 16:22
@File   :   test_app_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """AppHandler测试类"""

    @pytest.mark.parametrize(
        "app_id, query",
        [
            ("23ca97c3-a6a2-4bb8-8b2b-4b2c8a4fd5f0", "你好，你是谁？"),
            ("23ca97c3-a6a2-4bb8-8b2b-4b2c8a4fd5f0", None),
        ]
    )
    def test_debug(self, app_id, query, client):
        response = client.post(f"/apps/{app_id}/debug", json={"query": query})
        # 测试接口返回成功
        assert response.status_code == 200

        if query is None:
            # 测试数据校验失败
            assert response.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            # 测试completion返回成功
            assert response.json.get("code") == HttpCode.SUCCESS

        print("返回响应：", response.json)
