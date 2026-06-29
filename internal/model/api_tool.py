#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API工具模型类

@Author :   Xinkang Wu
@Time   :   2026/6/28 14:54
@File   :   api_tool.py
"""
from sqlalchemy import PrimaryKeyConstraint, Column, UUID, text, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class ApiToolProvider(db.Model):
    """API工具提供者模型"""
    __tablename__ = "api_tool_provider"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    openapi_schema = Column(Text, nullable=False, server_default=text("''::text"))
    headers = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class ApiTool(db.Model):
    """API工具模型"""
    __tablename__ = "api_tool"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    provider_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    url = Column(String(255), nullable=False, server_default=text("''::character varying"))
    method = Column(String(255), nullable=False, server_default=text("''::character varying"))
    parameters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def provider(self) -> "ApiToolProvider":
        """当前工具的服务提供者（只读）"""
        return db.session.query(ApiToolProvider).get(self.provider_id)
