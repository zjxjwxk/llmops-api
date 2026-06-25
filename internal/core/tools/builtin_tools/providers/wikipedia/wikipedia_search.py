#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
维基百科搜索工具

@Author :   Xinkang Wu
@Time   :   2026/6/22 21:30
@File   :   wikipedia_search.py
"""
from langchain_community.tools.wikipedia.tool import WikipediaQueryInput, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


@add_attribute("args_schema", WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """返回维基百科搜索工具"""
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper()
    )
