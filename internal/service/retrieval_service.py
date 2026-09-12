#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检索服务

@Author :   Xinkang Wu
@Time   :   2026/8/15 22:05
@File   :   retrieval_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document as LangChainDocument
from sqlalchemy import update

from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
from internal.exception import NotFoundException
from internal.model import Dataset, DatasetQuery, Segment
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jieba_service import JiebaService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class RetrievalService(BaseService):
    """检索服务"""

    db: SQLAlchemy
    vector_database_service: VectorDatabaseService
    jieba_service: JiebaService

    def search_in_datasets(
            self,
            dataset_ids: list[UUID],
            query: str,
            retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
            k: int = 4,
            score: float = 0,
            retrieval_source: str = RetrievalSource.HIT_TESTING
    ) -> list[LangChainDocument]:
        """知识库检索"""

        # TODO: 实现授权认证模块后，完善账户相关逻辑
        account_id = "05a9c691-a5b0-4661-893a-430c760eb8cd"

        # 获取知识库列表并校验权限
        datasets = self.db.session.query(Dataset).filter(
            Dataset.id.in_(dataset_ids),
            Dataset.account_id == account_id
        ).all()

        if datasets is None or len(datasets) == 0:
            raise NotFoundException("知识库不存在或当前用户无权访问")

        # 更新为实际存在的知识库ID列表
        dataset_ids = [dataset.id for dataset in datasets]

        # 构建检索器
        from internal.core.retrievers import SemanticRetriever, FullTextRetriever
        semantic_retriever = SemanticRetriever(
            dataset_ids=dataset_ids,
            vector_store=self.vector_database_service.vector_store,
            search_kwargs={
                "k": k,
                "score_threshold": score,
            }
        )
        full_text_retriever = FullTextRetriever(
            db=self.db,
            dataset_ids=dataset_ids,
            jieba_service=self.jieba_service,
            search_kwargs={
                "k": k
            }
        )
        hybrid_retriever = EnsembleRetriever(
            retrievers=[semantic_retriever, full_text_retriever],
            weights=[0.5, 0.5]
        )

        # 根据检索策略进行检索
        if retrieval_strategy == RetrievalStrategy.SEMANTIC:
            langchain_documents = semantic_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.FULL_TEXT:
            langchain_documents = full_text_retriever.invoke(query)[:k]
        else:
            langchain_documents = hybrid_retriever.invoke(query)[:k]

        # 创建知识库查询记录（每个知识库记录一条）
        dataset_id_set = list(
            set(str(langchain_document.metadata["dataset_id"]) for langchain_document in langchain_documents)
        )
        for dataset_id in dataset_id_set:
            self.create(
                DatasetQuery,
                dataset_id=dataset_id,
                query=query,
                source=retrieval_source,
                # TODO: App配置模块完成后实现
                source_app_id=None,
                created_by=account_id,
            )

        # 批量更新片段命中次数
        with self.db.auto_commit():
            statement = (
                update(Segment)
                .where(Segment.id.in_(
                    [langchain_document.metadata["segment_id"] for langchain_document in langchain_documents]))
                .values(hit_count=Segment.hit_count + 1)
            )
            self.db.session.execute(statement)

        return langchain_documents
