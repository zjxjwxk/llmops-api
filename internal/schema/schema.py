#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义WTForms字段

@Author :   Xinkang Wu
@Time   :   2026/6/29 15:01
@File   :   schema.py
"""
from wtforms import Field


class ListField(Field):
    """自定义List字段，表示列表数据"""
    data: list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data else []
