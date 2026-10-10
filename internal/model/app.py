#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/25 20:47
@File   :   app.py
"""

from sqlalchemy import Column, UUID, String, Text, DateTime, PrimaryKeyConstraint, text, Integer
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class App(db.Model):
    """应用模型模型"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)  # 创建账号id
    app_config_id = Column(UUID, nullable=True)  # 发布配置id，未发布应用时为空
    draft_app_config_id = Column(UUID, nullable=True)  # 草稿配置id，新建应用时为空
    debug_conversation_id = Column(UUID, nullable=True)  # 调试会话id，为None则代表没有会话信息
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用名称
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用图标
    description = Column(Text, nullable=False, server_default=text("''::text"))  # 应用描述
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用状态
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class AppConfig(db.Model):
    """应用配置模型"""
    __tablename__ = "app_config"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 携带对话轮数
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 预设Prompt
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工具列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工作流列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 知识库检索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 长期记忆配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 开场白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 开场白建议问题列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 语音转文本配置
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本转语音配置
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 审核配置
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class AppConfigVersion(db.Model):
    """应用配置版本历史模型（用于存储草稿配置+历史发布配置）"""
    __tablename__ = "app_config_version"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_version_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 携带对话轮数
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 预设Prompt
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工具列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工作流列表
    datasets = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的知识库列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 知识库检索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 长期记忆配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 开场白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 开场白建议问题列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 语音转文本配置
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本转语音配置
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 审核配置
    version = Column(Integer, nullable=False, server_default=text("0"))  # 发布版本号
    config_type = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 配置类型
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class AppDataset(db.Model):
    """应用知识库关联模型"""

    __tablename__ = "app_dataset"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
