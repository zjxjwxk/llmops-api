#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义API工具处理器测试类

@Author :   Xinkang Wu
@Time   :   2026/6/28 17:59
@File   :   test_api_tool_handler.py
"""
import pytest

from internal.model import ApiToolProvider
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
						"description": "请求服务权限标识",
						"required": true,
						"type": "str"
					},
					{
						"name": "keywords",
						"in": "query",
						"description": "查询关键字",
						"required": true,
						"type": "str"
					},
					{
						"name": "subdistrict",
						"in": "query",
						"description": "子级行政区",
						"required": false,
						"type": "int"
					}
				]
			}
		},
		"/weather/weatherInfo": {
			"get": {
				"description": "天气查询",
				"operationId": "GetWeatherInfo",
				"parameters": [
					{
						"name": "key",
						"in": "query",
						"description": "请求服务权限标识",
						"required": true,
						"type": "str"
					},
					{
						"name": "city",
						"in": "query",
						"description": "城市编码",
						"required": true,
						"type": "str"
					},
					{
						"name": "extensions",
						"in": "query",
						"description": "气象类型",
						"required": false,
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

        resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": openapi_schema})
        assert resp.status_code == 200
        if openapi_schema == "123":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        elif openapi_schema == self.valid_openapi_schema:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("provider_id", [
        "a712e526-f4dd-490f-be3e-256d581c201c",
        "a712e526-f4dd-490f-be3e-256d581c201d"
    ])
    def test_get_api_tool_provider(self, provider_id, client):
        """测试获取自定义API工具提供商"""

        resp = client.get(f"/api-tools/{provider_id}")
        assert resp.status_code == 200
        if provider_id.endswith("c"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif provider_id.endswith("d"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("query", [
        {},
        {"current_page": 5},
        {"search_word": "高德"},
        {"search_word": "百度"},
    ])
    def test_get_api_tool_providers_with_page(self, query, client):
        """测试获取自定义API工具提供商分页"""

        resp = client.get("/api-tools", query_string=query)
        assert resp.status_code == 200
        if query.get("current_page") == 5:
            assert len(resp.json.get("data").get("list")) == 0
        elif query.get("search_word") == "高德":
            assert len(resp.json.get("data").get("list")) == 1
        elif query.get("search_word") == "百度":
            assert len(resp.json.get("data").get("list")) == 0
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("provider_id, tool_name", [
        ("a712e526-f4dd-490f-be3e-256d581c201c", "GetWeatherInfo"),
        ("a712e526-f4dd-490f-be3e-256d581c201c", "GetPrice")
    ])
    def test_get_api_tool(self, provider_id, tool_name, client):
        """测试获取自定义API工具"""

        resp = client.get(f"/api-tools/{provider_id}/tools/{tool_name}")
        assert resp.status_code == 200
        if tool_name == "GetWeatherInfo":
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif tool_name == "GetPrice":
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_create_api_tool_provider(self, client, db):
        """测试创建自定义API工具提供商"""

        data = {
            "name": "单元测试工具包",
            "icon": "http://127.0.0.1:5001/builtin-tools/amap/icon",
            "openapi_schema": self.valid_openapi_schema,
            "headers": [{"key": "Content-Type", "value": "application/json; charset=utf-8"}]
        }
        resp = client.post("/api-tools", json=data)
        assert resp.status_code == 200

        api_tool_provider = db.session.query(ApiToolProvider).filter_by(name="单元测试工具包").one_or_none()
        assert api_tool_provider is not None

    def test_delete_api_tool_provider(self, client, db):
        """测试删除自定义API工具提供商"""

        provider_id = "a712e526-f4dd-490f-be3e-256d581c201c"
        resp = client.post(f"/api-tools/{provider_id}/delete")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider is None

    def test_update_api_tool_provider(self, client, db):
        """测试更新自定义API工具提供商"""

        provider_id = "a712e526-f4dd-490f-be3e-256d581c201c"
        data = {
            "name": "更新后的高德API工具包",
            "icon": "http://127.0.0.1:5001/builtin-tools/amap/icon",
            "openapi_schema": self.valid_openapi_schema,
            "headers": [{"key": "Content-Type", "value": "application/json; charset=utf-8"}]
        }
        resp = client.post(f"/api-tools/{provider_id}", json=data)
        assert resp.status_code == 200

        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider.name == data.get("name")
