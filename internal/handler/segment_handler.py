#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档片段处理器

@Author :   Xinkang Wu
@Time   :   2026/8/11 20:48
@File   :   segment_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.segment_schema import GetSegmentsWithPageReq, GetSegmentsWithPageResp, GetSegmentResp, \
    UpdateSegmentEnabledReq, CreateSegmentReq, UpdateSegmentReq
from internal.service import SegmentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class SegmentHandler:
    """文档片段处理器"""

    segment_service: SegmentService

    @login_required
    def create_segment(self, dataset_id: UUID, document_id: UUID):
        """创建文档片段"""

        # 提取请求并校验
        req = CreateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建文档片段
        self.segment_service.create_segment(dataset_id, document_id, req, current_user)

        return success_message("创建文档片段成功")

    @login_required
    def get_segments_with_page(self, dataset_id: UUID, document_id: UUID):
        """获取文档片段列表分页"""

        # 提取请求并校验
        req = GetSegmentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务获取文档片段列表分页
        segments, paginator = self.segment_service.get_segments_with_page(dataset_id, document_id, req, current_user)

        resp = GetSegmentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(segments), paginator=paginator))

    @login_required
    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """获取文档片段详情"""

        segment = self.segment_service.get_segment(dataset_id, document_id, segment_id, current_user)

        resp = GetSegmentResp()
        return success_json(resp.dump(segment))

    @login_required
    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """更新文档片段信息"""

        # 提取请求并校验
        req = UpdateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新文档片段信息
        self.segment_service.update_segment(dataset_id, document_id, segment_id, req, current_user)

        return success_message("更新文档片段成功")

    @login_required
    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """更新文档片段启用状态"""

        # 提取请求并校验
        req = UpdateSegmentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更新文档片段启用状态
        self.segment_service.update_segment_enabled(dataset_id, document_id, segment_id, req.enabled.data, current_user)

        return success_message("更新文档片段启用状态成功")

    @login_required
    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """删除文档片段"""

        self.segment_service.delete_segment(dataset_id, document_id, segment_id, current_user)

        return success_message("删除文档片段成功")
