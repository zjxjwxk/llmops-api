#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档片段服务

@Author :   Xinkang Wu
@Time   :   2026/8/11 21:54
@File   :   segment_service.py
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LangChainDocument
from redis import Redis
from sqlalchemy import asc, func

from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import SegmentStatus, DocumentStatus
from internal.exception import NotFoundException, FailException, ValidationException
from internal.lib.helper import generate_text_hash
from internal.model import Segment, Document, Account
from internal.schema.segment_schema import GetSegmentsWithPageReq, CreateSegmentReq, UpdateSegmentReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class SegmentService(BaseService):
    """文档片段服务"""

    db: SQLAlchemy
    redis_client: Redis
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    vector_database_service: VectorDatabaseService
    keyword_table_service: KeywordTableService

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq, account: Account):
        """创建文档片段"""

        # 校验片段的内容token长度不能超过1000
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidationException("文档片段内容长度不能超过 1000 token")

        # 获取文档信息并校验
        document = self.get(Document, document_id)
        if document is None or document.account_id != account.id or document.dataset_id != dataset_id:
            raise NotFoundException("该知识库文档不存在或当前用户无权访问")

        # 判断文档当前是否可新增片段（仅限构建完成状态）
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("当前文档片段未构建完成，请稍后重试")

        # 获取文档片段最大位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id
        ).scalar()

        # 若未传入任何关键词，则调用jieba服务提取关键词列表
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        segment = None
        position += 1
        try:
            # 创建文档片段记录
            segment = self.create(
                Segment,
                account_id=account.id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=uuid.uuid4(),
                position=position,
                content=req.content.data,
                character_count=len(req.content.data),
                token_count=token_count,
                keywords=req.keywords.data,
                hash=generate_text_hash(req.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )

            # 写入向量数据库
            self.vector_database_service.vector_store.add_documents(
                [LangChainDocument(
                    page_content=req.content.data,
                    metadata={
                        "account_id": str(account.id),
                        "dataset_id": str(dataset_id),
                        "document_id": str(document_id),
                        "segment_id": str(segment.id),
                        "node_id": str(segment.node_id),
                        "document_enabled": document.enabled,
                        "segment_enabled": True,
                    }
                )],
                ids=[str(segment.node_id)]
            )

            # 更新文档的字符总数和token总数
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0),
            ).filter(
                Segment.document_id == document.id
            ).first()

            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count,
            )

            # 更新关键词表
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_segment_ids(dataset_id, [segment.id])
        except Exception as e:
            logging.exception(f"创建文档片段失败，错误信息：{str(e)}")
            if segment:
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now()
                )
                raise FailException("创建文档片段失败，请稍后重试")

    def get_segments_with_page(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: GetSegmentsWithPageReq,
            account: Account
    ) -> tuple[list[Segment], Paginator]:
        """获取文档片段列表分页"""

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or document.account_id != account.id:
            raise NotFoundException("该知识库文档不存在或当前用户无权访问")

        # 构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        # 执行分页查询
        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account):
        """获取文档片段详情"""

        # 获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在或当前用户无权访问")

        return segment

    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, req: UpdateSegmentReq,
                       account: Account):
        """更新文档片段信息"""

        # 校验片段的内容token长度不能超过1000
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidationException("文档片段内容长度不能超过 1000 token")

        # 获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在或当前用户无权修改")

        # 判断文档片段当前是否可启用（仅构建完成后才可启用）
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前文档片段未构建完成，请稍后重试")

        # 若未传入任何关键词，则调用jieba服务提取关键词列表
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 计算新内容hash值，判断是否需要更新文档信息及向量数据库
        new_hash = generate_text_hash(req.content.data)
        update_required = segment.hash != new_hash

        try:
            # 更新文档片段信息
            self.update(
                segment,
                keywords=req.keywords.data,
                content=req.content.data,
                hash=new_hash,
                character_count=len(req.content.data),
                token_count=token_count,
            )

            # 更新关键词表
            self.keyword_table_service.delete_keyword_table_from_segment_ids(dataset_id, [segment_id])
            self.keyword_table_service.add_keyword_table_from_segment_ids(dataset_id, [segment_id])

            # 判断是否需要更新文档信息及向量数据库
            if update_required:
                document = segment.document

                # 更新文档的字符总数和token总数
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0),
                ).filter(
                    Segment.document_id == document.id
                ).first()

                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )

                # 更新向量数据库
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={"text": req.content.data},
                    vector=self.embeddings_service.embeddings.embed_query(req.content.data),
                )
        except Exception as e:
            logging.exception(f"更新文档片段信息失败，segment_id：{segment_id}, 错误信息：{str(e)}")
            raise FailException("更新文档片段信息失败，请稍后重试")

        return segment

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, enabled: bool,
                               account: Account) -> None:
        """更新文档片段启用状态"""

        # 获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在或当前用户无权修改")

        # 判断文档片段当前是否可启用（仅构建完成后才可启用）
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前文档片段未构建完成，请稍后重试")

        # 判断文档片段启用状态是否需要更新
        if segment.enabled == enabled:
            raise FailException(f"更新文档片段启用状态错误，当前已为{'启用' if enabled else '禁用'}状态")

        # 获取分布式锁
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("当前文档片段正在更新启用状态，请稍后重试")

        with self.redis_client.lock(cache_key, LOCK_EXPIRE_TIME):
            try:
                # 更新文档片段启用状态至DB
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=None if enabled else datetime.now(),
                )

                # 更新知识库的关键词表
                document = segment.document
                if enabled is True and document.enabled is True:
                    # 启用片段，则新增关键词中的片段
                    self.keyword_table_service.add_keyword_table_from_segment_ids(dataset_id, [segment_id])
                else:
                    # 禁用片段，则删除关键词中的片段
                    self.keyword_table_service.delete_keyword_table_from_segment_ids(dataset_id, [segment_id])

                # 更新文档片段启用状态至向量数据库
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id,
                    properties={"segment_enabled": enabled},
                )
            except Exception as e:
                logging.exception(f"更新文档片段启用状态失败，文档片段ID：{segment_id}，错误信息：{str(e)}")
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now()
                )
                raise FailException("更新文档片段启用状态失败，请稍后重试")

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """删除文档片段"""

        # 获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在或当前用户无权删除")

        # 判断文档片段当前是否可删除（仅构建完成或失败才可启用）
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("当前文档片段未构建完成，请稍后重试")

        document = segment.document

        # 删除文档片段
        self.delete(segment)

        # 删除关键词表中的片段
        self.keyword_table_service.delete_keyword_table_from_segment_ids(dataset_id, [segment_id])

        # 删除向量数据库中的片段
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(f"删除向量数据库中的文档片段失败，segment_id：{segment_id}，错误信息：{str(e)}")

        # 更新文档信息（字符总数、Token总数）
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0),
        ).filter(
            Segment.document_id == document.id
        ).first()

        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment
