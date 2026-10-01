#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件上传处理器

@Author :   Xinkang Wu
@Time   :   2026/7/16 12:50
@File   :   upload_file_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.upload_file_schema import UploadFileReq, UploadFileResp, UploadImageReq
from internal.service import OciObjectStorageService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UploadFileHandler:
    """文件上传处理器"""

    oci_object_storage_service: OciObjectStorageService

    @login_required
    def upload_file(self):
        """上传文件"""

        # 构建请求并校验
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 上传文件至OCI对象存储服务并获取记录
        upload_file = self.oci_object_storage_service.upload_file(req.file.dataFalse, False, current_user)

        # 构建响应并返回
        resp = UploadFileResp()
        return success_json(resp.dump(upload_file))

    @login_required
    def upload_image(self):
        """上传图片"""

        # 构建请求并校验
        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 上传图片至OCI对象存储服务并获取记录
        upload_file = self.oci_object_storage_service.upload_file(req.file.data, True, current_user)

        # 获取图片URL地址
        image_url = self.oci_object_storage_service.get_file_url(upload_file.key)

        return success_json({"image_url": image_url})
