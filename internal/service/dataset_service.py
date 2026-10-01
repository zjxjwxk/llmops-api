#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库服务

@Author :   Xinkang Wu
@Time   :   2026/7/26 15:57
@File   :   dataset_service.py
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidationException, NotFoundException, FailException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset, Segment, DatasetQuery, AppDataset, Account
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq, HitReq
from internal.task.dataset_task import delete_dataset
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .retrieval_service import RetrievalService


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""

    db: SQLAlchemy
    retrieval_service: RetrievalService

    def create_dataset(self, req: CreateDatasetReq, account: Account) -> Dataset:
        """创建知识库"""

        # 检查当前账户是否已存在同名知识库
        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account.id,
            name=req.name.data,
        ).one_or_none()

        if dataset:
            raise ValidationException(f"该知识库名称{req.name.data}已存在")

        # 设置默认描述
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 创建知识库记录
        return self.create(
            Dataset,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

    def get_dataset(self, dataset_id: UUID, account: Account):
        """获取知识库"""

        # 检查当前账户是否存在该知识库
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq, account: Account) -> tuple[list[Dataset], Paginator]:
        """获取知识库分页"""

        # 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Dataset.account_id == account.id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        # 分页查询数据
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at")),
        )

        return datasets, paginator

    def get_dataset_queries(self, dataset_id: UUID, account: Account) -> list[DatasetQuery]:
        """获取知识库最近查询记录列表"""

        # 检查当前账户是否存在该知识库
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 获取知识库最近查询记录列表
        dataset_queries = self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id
        ).order_by(desc("created_at")).limit(10).all()

        return dataset_queries

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq, account: Account) -> Dataset:
        """更新知识库"""

        # 检查当前账户是否存在该知识库
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 检查更新后的知识库名称是否已存在（不包括当前请求的dataset_id）
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account.id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id,
        ).one_or_none()

        if check_dataset:
            raise ValidationException(f"该知识库名称{req.name.data}已存在")

        # 设置默认描述
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 更新知识库
        self.update(
            dataset,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

        return dataset

    def hit(self, dataset_id: UUID, req: HitReq, account: Account) -> list[dict]:
        """知识库召回测试"""

        # 检查当前账户是否存在该知识库
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 调用检索服务检索LangChain文档列表（结果已排序）
        langchain_documents = self.retrieval_service.search_in_datasets(
            dataset_ids=[dataset_id],
            account=account,
            **req.data,
        )
        langchain_documents_dict = {
            str(langchain_document.metadata["segment_id"]): langchain_document
            for langchain_document in langchain_documents
        }

        # 查询文档片段列表
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_(
                str(langchain_document.metadata["segment_id"]) for langchain_document in langchain_documents),
        ).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 排序片段列表（根据有序的LangChain文档列表构建）
        sorted_segments = [
            segment_dict[str(langchain_document.metadata["segment_id"])]
            for langchain_document in langchain_documents if
            str(langchain_document.metadata["segment_id"]) in segment_dict
        ]

        # 构建响应
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                },
                "dataset_id": segment.dataset_id,
                "score": langchain_documents_dict[str(segment.id)].metadata["score"],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result

    def delete_dataset(self, dataset_id: UUID, account: Account):
        """删除知识库（包括其应用关联记录、文档记录、片段记录、关键词记录、知识库查询记录、向量数据库数据）"""

        # 检查当前账户是否存在该知识库
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        try:
            # 删除知识库记录
            self.delete(dataset)

            # 删除应用知识库关联记录
            with self.db.auto_commit():
                self.db.session.query(AppDataset).filter(
                    AppDataset.dataset_id == dataset_id,
                ).delete()

            # 调用异步任务，删除文档记录、片段记录、关键词表记录、知识库查询记录、向量数据库数据
            delete_dataset.delay(dataset_id)

        except Exception as e:
            logging.exception(f"删除知识库失败，dataset_id：{dataset_id}，错误信息：{str(e)}")
            raise FailException("删除知识库失败，请稍后重试")
