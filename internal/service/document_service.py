#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档服务

@Author :   Xinkang Wu
@Time   :   2026/7/31 17:22
@File   :   document_service.py
"""
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from redis import Redis
from sqlalchemy import desc, asc, func

from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import ProcessType, SegmentStatus, DocumentStatus
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException, NotFoundException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Document, Dataset, UploadFile, ProcessRule, Segment, Account
from internal.schema.document_schema import GetDocumentsWithPageReq
from internal.service import BaseService
from internal.task.document_task import build_documents, update_document_enabled, delete_document
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DocumentService(BaseService):
    """文档服务"""

    db: SQLAlchemy
    redis_client: Redis

    def create_documents(
            self,
            dataset_id: UUID,
            upload_file_ids: list[UUID],
            account: Account,
            process_type: str = ProcessType.AUTOMATIC,
            rule: dict = None,
    ) -> tuple[list[Document], str]:
        """创建文档列表，并调用异步任务"""

        # 校验知识库权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise ForbiddenException("该知识库不存在或当前用户无权访问")

        # 提取文件并校验文件权限和扩展名
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account.id,
            UploadFile.id.in_(upload_file_ids)
        ).all()

        upload_files = [upload_file for upload_file in upload_files
                        if upload_file.extension.lower() in ALLOWED_DOCUMENT_EXTENSION]

        if len(upload_files) == 0:
            logging.warning(
                f"上传文档列表时，未找到任何合法文件，account_id: {str(account.id)}, dataset_id: {dataset_id}, upload_file_ids: {upload_file_ids}")
            raise FailException("未找到任何合法文件，请重新上传")

        # 创建批次与处理规则
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account.id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule,
        )

        # 获取知识库的最新文档位置
        position = self.get_latest_document_position(dataset_id)

        # 创建文档列表记录
        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account.id,
                dataset_id=dataset_id,
                upload_file_id=upload_file.id,
                process_rule_id=process_rule.id,
                batch=batch,
                name=upload_file.name,
                position=position,
            )
            documents.append(document)

        build_documents.delay([document.id for document in documents])

        return documents, batch

    def get_document(self, dataset_id: UUID, document_id: UUID, account: Account) -> Document:
        """获取文档详情"""

        # 查询文档记录
        document = self.get(Document, document_id)

        if document is None:
            raise NotFoundException("该文档不存在，请检查后重试")

        if document.dataset_id != dataset_id or str(document.account_id) != account.id:
            raise ForbiddenException("当前用户无权限查看该文档，请检查后重试")

        return document

    def get_documents_with_page(
            self, dataset_id: UUID,
            req: GetDocumentsWithPageReq,
            account: Account
    ) -> tuple[list[Document], Paginator]:
        """获取文档列表分页"""

        # 校验知识库权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise ForbiddenException("该知识库不存在或当前用户无权访问")

        # 构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [
            Document.account_id == account.id,
            Document.dataset_id == dataset_id,
        ]
        if req.search_word.data:
            filters.append(Document.name.ilike(f"%{req.search_word.data}%"))

        # 执行分页查询
        documents = paginator.paginate(
            self.db.session.query(Document).filter(*filters).order_by(desc("created_at"))
        )

        return documents, paginator

    def get_documents_status(self, dataset_id: UUID, batch: str, account: Account) -> list[dict]:
        """获取文档列表状态（根据知识库和批次）"""

        # 校验知识库权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise ForbiddenException("该知识库不存在或当前用户无权访问")

        # 查询该批次文档列表
        documents = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
            Document.batch == batch,
        ).order_by(asc("position")).all()

        if documents is None or len(documents) == 0:
            raise NotFoundException("该处理批次未找到文档，请检查并重试")

        # 查询列表中所有文档的状态
        documents_status = []
        for document in documents:
            # 查询文档总片段数和已完成构建片段数
            segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
            ).scalar()

            completed_segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
                Segment.status == SegmentStatus.COMPLETED,
            ).scalar()

            upload_file = document.upload_file
            documents_status.append({
                "id": document.id,
                "name": document.name,
                "size": upload_file.size,
                "extension": upload_file.extension,
                "mime_type": upload_file.mime_type,
                "position": document.position,
                "segment_count": segment_count,
                "completed_segment_count": completed_segment_count,
                "error": document.error,
                "status": document.status,
                "processing_started_at": datetime_to_timestamp(document.processing_started_at),
                "parsing_completed_at": datetime_to_timestamp(document.parsing_completed_at),
                "splitting_completed_at": datetime_to_timestamp(document.splitting_completed_at),
                "indexing_completed_at": datetime_to_timestamp(document.indexing_completed_at),
                "completed_at": datetime_to_timestamp(document.completed_at),
                "stopped_at": datetime_to_timestamp(document.stopped_at),
                "created_at": datetime_to_timestamp(document.created_at)
            })

        return documents_status

    def update_document(self, dataset_id: UUID, document_id: UUID, account: Account, **kwargs):
        """更新文档信息"""

        # 查询文档记录
        document = self.get(Document, document_id)

        if document is None:
            raise NotFoundException("该文档不存在，请检查后重试")

        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("当前用户无权限修改该文档，请检查后重试")

        return self.update(document, **kwargs)

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID, enabled: bool, account: Account) -> Document:
        """更新文档启用状态（同时异步更新至向量数据库）"""

        # 获取文档并校验权限
        document = self.get(Document, document_id)

        if document is None:
            raise NotFoundException("该文档不存在，请检查后重试")

        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("当前用户无权限修改该文档，请检查后重试")

        # 判断文档当前是否可启用（仅构建完成后才可启用）
        if document.status != DocumentStatus.COMPLETED:
            raise ForbiddenException("当前文档未构建完成，请稍后重试启用")

        # 判断文档启用状态是否需要更新
        if document.enabled == enabled:
            raise FailException(f"更新文档启用状态错误，当前已为{'启用' if enabled else '禁用'}状态")

        # 获取分布式锁
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document.id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("当前文档正在更新启用状态，请稍后重试")

        # 更新文档启用状态至DB
        self.update(
            document,
            enabled=enabled,
            disabled_at=None if enabled else datetime.now(),
        )

        # 设置分布式锁，过期时间默认为600秒
        self.redis_client.setex(cache_key, LOCK_EXPIRE_TIME, 1)

        # 调用异步任务，更新文档启用状态至向量数据库
        update_document_enabled.delay(document.id)

        return document

    def get_latest_document_position(self, dataset_id: UUID) -> int:
        """获取知识库的最新文档位置"""

        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
        ).order_by(desc("position")).first()

        return document.position if document else 0

    def delete_document(self, dataset_id: UUID, document_id: UUID, account: Account) -> Document:
        """删除文档（包括删除文档片段、更新关键词表、删除向量数据库记录）"""

        # 获取文档并校验权限
        document = self.get(Document, document_id)

        if document is None:
            raise NotFoundException("该文档不存在，请检查后重试")

        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("当前用户无权限修改该文档，请检查后重试")

        # 判读文档是否处于可删除状态（构建完成/构建错误）
        if document.status not in [DocumentStatus.COMPLETED, DocumentStatus.ERROR]:
            raise FailException("当前文档处于不可删除状态，请稍后重试")

        # 删除文档
        self.delete(document)

        # 调用异步任务，执行后续操作：删除文档片段、更新关键词表、删除向量数据库记录
        delete_document.delay(dataset_id, document_id)

        return document
