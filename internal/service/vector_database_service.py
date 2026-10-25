#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
向量数据库服务

@Author :   Xinkang Wu
@Time   :   2026/5/4 20:41
@File   :   vector_database_service.py
"""
import os

import weaviate
from injector import inject, singleton
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.client import WeaviateClient
from weaviate.collections import Collection

from internal.service.embeddings_service import EmbeddingsService

# 向量数据库集合名称
COLLECTION_NAME = "Dataset"


@inject
@singleton
class VectorDatabaseService:
    """向量数据库服务"""

    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        self.embeddings_service = embeddings_service

        # 延迟连接Weaviate并创建向量数据库，避免应用启动时加载嵌入模型
        self._client: WeaviateClient | None = None
        self._vector_store: WeaviateVectorStore | None = None

    @property
    def client(self) -> WeaviateClient:
        if self._client is None:
            self._client = weaviate.connect_to_local(
                host=os.getenv("WEAVIATE_HOST"),
                port=int(os.getenv("WEAVIATE_PORT")),
            )
        return self._client

    @property
    def vector_store(self) -> WeaviateVectorStore:
        if self._vector_store is None:
            self._vector_store = WeaviateVectorStore(
                client=self.client,
                index_name=COLLECTION_NAME,
                text_key="text",
                embedding=self.embeddings_service.cache_backed_embeddings
            )
        return self._vector_store

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @property
    def collection(self) -> Collection:
        return self.client.collections.get(COLLECTION_NAME)
