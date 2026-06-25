#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Serper API

@Author :   Xinkang Wu
@Time   :   2026/6/21 15:05
@File   :   google_serper.py
"""
from langchain_community.tools import GoogleSerperRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


@add_attribute("args_schema", GoogleSerperArgsSchema)
def google_serper(**kwargs) -> BaseTool:
    """Google Serper API"""
    return GoogleSerperRun(
        name="google_serper",
        description="一个低成本的谷歌搜索API",
        args_schema=GoogleSerperArgsSchema
    )
