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
from injector import inject
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.client import WeaviateClient
from weaviate.collections import Collection

from .embeddings_service import EmbeddingsService

# 向量数据库集合名称
COLLECTION_NAME = "Dataset"


@inject
class VectorDatabaseService:
    """向量数据库服务"""

    client: WeaviateClient
    vector_store: WeaviateVectorStore
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        self.embeddings_service = embeddings_service

        # 创建并连接Weaviate向量数据库
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT")),
        )

        # 创建LangChain向量数据库
        self.vector_store = WeaviateVectorStore(
            self.client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=self.embeddings_service.embeddings
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @property
    def collection(self) -> Collection:
        return self.client.collections.get(COLLECTION_NAME)
