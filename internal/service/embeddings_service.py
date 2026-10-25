#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本嵌入服务

@Author :   Xinkang Wu
@Time   :   2026/7/27 21:44
@File   :   embeddings_service.py
"""
import os
from dataclasses import dataclass

import tiktoken
from injector import inject, singleton
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis


@inject
@singleton
@dataclass
class EmbeddingsService:
    """文本嵌入服务"""

    _store: RedisStore
    _embeddings: Embeddings | None
    _cache_backed_embeddings: CacheBackedEmbeddings | None

    def __init__(self, redis: Redis):
        """构造函数"""

        self._store = RedisStore(client=redis)
        self._embeddings = None
        self._cache_backed_embeddings = None

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算文本token数"""

        encoding = tiktoken.encoding_for_model("text-embedding-3-large")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name="Alibaba-NLP/gte-multilingual-base",
                cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
                model_kwargs={
                    "trust_remote_code": True
                },
            )
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        if self._cache_backed_embeddings is None:
            self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
                self.embeddings,
                self._store,
                namespace="embeddings",
            )
        return self._cache_backed_embeddings
