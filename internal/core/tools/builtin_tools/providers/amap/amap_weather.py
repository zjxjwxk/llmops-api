#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高德天气预报查询工具

@Author :   Xinkang Wu
@Time   :   2026/6/22 21:24
@File   :   amap_weather.py
"""
import json
import os
from typing import Any, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class AmapWeatherArgsSchema(BaseModel):
    city: str = Field(description="需要查询天气预报的目标城市，例如：杭州")


class AmapWeatherTool(BaseTool):
    """根据传入的城市名查询天气"""

    name: str = "amap_weather_tool"
    description: str = "天气预报查询工具"
    args_schema: Type[BaseModel] = AmapWeatherArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """根据传入的城市名称调用高德API获取城市对应的天气预报信息"""
        try:
            # 获取高德API Key
            amap_api_key = os.getenv("AMAP_API_KEY")
            if not amap_api_key:
                return f"未配置高德API Key"

            # 从参数中获取城市名称
            city = kwargs.get("city", "")

            amap_api_url = os.getenv("AMAP_API_URL")
            session = requests.session()

            # 调用行政区域编码查询API，根据city获取ad_code
            city_response = session.request(
                method="GET",
                url=f"{amap_api_url}/config/district?key={amap_api_key}&keywords={city}&subdistrict=0",
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            city_response.raise_for_status()
            city_data = city_response.json()
            if city_data.get("info") == "OK":
                ad_code = city_data["districts"][0]["adcode"]
            else:
                return f"获取{city}行政区域编码失败"

            # 调用天气预报查询API，根据ad_code获取天气预报
            weather_response = session.request(
                method="GET",
                url=f"{amap_api_url}/weather/weatherInfo?key={amap_api_key}&city={ad_code}&extensions=all",
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            if weather_data.get("info") == "OK":
                # 返回JSON字符串结果
                return json.dumps(weather_data)
            else:
                return f"获取{city}天气预报信息失败"
        except Exception:
            return f"获取{kwargs.get('city', '')}天气预报信息失败"


@add_attribute("args_schema", AmapWeatherArgsSchema)
def amap_weather(**kwargs) -> BaseTool:
    """获取高德天气预报工具"""
    return AmapWeatherTool()
