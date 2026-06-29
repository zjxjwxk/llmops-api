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
	"server": "https://restapi.amap.com/v3",
	"description": "高德地图API",
	"paths": {
		"/config/district": {
			"get": {
				"description": "获取行政区域编码",
				"operationId": "GetDistrictCode",
				"parameters": [
					{
						"name": "key",
						"in": "query",
						"description": "高德地图API Key",
						"required": true,
						"type": "str"
					},
					{
						"name": "keywords",
						"in": "query",
						"description": "城市名称",
						"required": true,
						"type": "str"
					}
				]
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
