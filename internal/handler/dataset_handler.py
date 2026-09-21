#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库处理器

@Author :   Xinkang Wu
@Time   :   2026/7/23 21:07
@File   :   dataset_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.model import UploadFile
from internal.schema.dataset_schema import CreateDatasetReq, GetDatasetResp, UpdateDatasetReq, GetDatasetsWithPageReq, \
    GetDatasetsWithPageResp, HitReq, GetDatasetQueriesResp
from internal.service import DatasetService, EmbeddingsService, JiebaService, VectorDatabaseService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    """知识库处理器"""

    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    vector_database_service: VectorDatabaseService
    db: SQLAlchemy

    def create_dataset(self):
        """创建知识库"""

        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建知识库
        self.dataset_service.create_dataset(req)

        return success_message("创建知识库成功")

    def get_dataset(self, dataset_id: UUID):
        """获取知识库"""

        # 调用服务获取知识库
        dataset = self.dataset_service.get_dataset(dataset_id)

        resp = GetDatasetResp()

        return success_json(resp.dump(dataset))

    @login_required
    def get_dataset_with_page(self):
        """获取知识库分页"""

        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务获取知识库分页
        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)

        # 构建分页响应
        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

    def get_dataset_queries(self, dataset_id: UUID):
        """获取知识库最近查询记录列表"""

        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id)

        resp = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))

    def update_dataset(self, dataset_id: UUID):
        """更新知识库"""

        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新知识库
        self.dataset_service.update_dataset(dataset_id, req)

        return success_message("更新知识库成功")

    def delete_dataset(self, dataset_id: UUID):
        """删除知识库"""

        self.dataset_service.delete_dataset(dataset_id)
        return success_message("删除知识库成功")

    def embeddings_query(self):
        upload_file = self.db.session.query(UploadFile).get("3eac1be9-c24e-4a85-8c30-4d30cf9f64e0")
        content = self.file_extractor.load(upload_file, True)
        return success_json({"content": content})

        # query = request.args.get("query")

        # vectors = self.embeddings_service.embeddings.embed_query(query)
        # return success_json({"vectors": vectors})

        # keywords = self.jieba_service.extract_keywords(query)
        # return success_json({"keywords": keywords})

    def hit(self, dataset_id: UUID):
        """知识库召回测试"""

        # 提取请求并校验
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务执行检索
        hit_result = self.dataset_service.hit(dataset_id, req)
        return success_json(hit_result)
