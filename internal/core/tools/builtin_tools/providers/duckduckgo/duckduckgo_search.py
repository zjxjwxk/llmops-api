#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DuckDuckGo搜索工具

@Author :   Xinkang Wu
@Time   :   2026/6/22 20:58
@File   :   duckduckgo_search.py
"""
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class DuckDuckGoSearchInput(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


@add_attribute("args_schema", DuckDuckGoSearchInput)
def duckduckgo_search(**kwargs) -> BaseTool:
    """返回DuckDuckGo搜索工具"""
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，但需要搜索时事时可以使用",
        args_schema=DuckDuckGoSearchInput,
    )
