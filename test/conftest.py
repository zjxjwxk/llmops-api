#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/24 16:43
@File   :   conftest.py
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker, scoped_session

# Mock the embeddings service before importing the app
mock_embeddings = Mock()
mock_store = Mock()
mock_cache_backed_embeddings = Mock()

with patch('internal.service.embeddings_service.HuggingFaceEmbeddings', return_value=mock_embeddings), \
     patch('internal.service.embeddings_service.RedisStore', return_value=mock_store), \
     patch('internal.service.embeddings_service.CacheBackedEmbeddings.from_bytes_store', return_value=mock_cache_backed_embeddings):
    from app.http.app import app as _app
    from internal.extension.database_extension import db as _db


@pytest.fixture
def app():
    """获取Flask应用实例"""
    _app.config["TESTING"] = True
    return _app


@pytest.fixture
def client(app):
    """获取Flask测试客户端实例"""
    with app.test_client() as client:
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNWE5YzY5MS1hNWIwLTQ2NjEtODkzYS00MzBjNzYwZWI4Y2QiLCJpc3MiOiJMTE1PcHMiLCJleHAiOjE3OTM0MjM4OTh9.WTzgCCewbsATvu8BYB-PwVJSSageMyIHhRRZ7Y003vU"
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        yield client


@pytest.fixture
def db(app):
    """创建临时数据库会话，测试结束后回滚数据"""
    with app.app_context():
        # 获取数据库连接并开启事务
        connection = _db.engine.connect()
        transaction = connection.begin()

        # 创建临时数据库会话
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session

        # 抛出数据库实例
        yield _db

        # 回滚数据
        transaction.rollback()
        # 关闭数据库连接
        connection.close()
        # 清除会话
        session.remove()
