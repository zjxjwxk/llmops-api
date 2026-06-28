#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具处理器测试类

@Author :   Xinkang Wu
@Time   :   2026/6/28 17:59
@File   :   test_api_tool_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestApiToolHandler:
    """自定义API工具处理器测试类"""

    valid_openapi_schema = """
{
	"server": "https://weather.example.com",
	"description": "天气工具",
	"paths": {
		"/location": {
			"get": {
				"description": "获取特定位置的天气预报信息",
				"operationId": "GetCurrentWeather",
				"parameters": [{
					"name": "location",
					"in": "query",
					"description": "需要获取天气预报的城市名",
					"required": true,
					"type": "str"
				}]
			}
		}
	}
}
    """

    @pytest.mark.parametrize("openapi_schema", ["123", valid_openapi_schema])
    def test_validate_openapi_schema(self, openapi_schema, client):
        """测试校验OpenAPI Schema"""
        response = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": openapi_schema})
        assert response.status_code == 200
        if openapi_schema == "123":
            assert response.json.get("code") == HttpCode.VALIDATE_ERROR
        elif openapi_schema == self.valid_openapi_schema:
            assert response.json.get("code") == HttpCode.SUCCESS
