#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCI对象存储服务

@Author :   Xinkang Wu
@Time   :   2026/7/16 13:20
@File   :   oci_object_storage_service.py
"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

import oci
from injector import inject
from oci.object_storage import ObjectStorageClient
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION, ALLOWED_IMAGE_EXTENSION
from internal.exception import FailException
from internal.model import UploadFile, Account
from .upload_file_service import UploadFileService


@inject
@dataclass
class OciObjectStorageService:
    """OCI对象存储服务"""

    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, only_image: bool, account: Account) -> UploadFile:
        """上传文件至OCI对象存储，返回文件信息"""

        # 提取文件扩展名并校验是否允许
        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension.lower() not in (ALLOWED_DOCUMENT_EXTENSION + ALLOWED_IMAGE_EXTENSION):
            raise FailException(f"不允许上传扩展为{extension}的文件")
        elif only_image and extension not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"不允许上传扩展为{extension}的图片")

        # 获取OCI客户端和存储桶名称
        client = self._get_client()
        bucket_namespace = self._get_oci_bucket_namespace()
        bucket_name = self._get_oci_bucket_name()

        # 生成一个随机文件名
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_file_name = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 流式读取上传文件并上传至OCI对象存储
        file_content = file.stream.read()
        try:
            client.put_object(
                namespace_name=bucket_namespace,
                bucket_name=bucket_name,
                object_name=upload_file_name,
                put_object_body=file_content,
                content_type=file.mimetype
            )
        except Exception:
            raise FailException("上传文件失败，请稍后重试")

        # 创建UploadFile记录
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_file_name,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, object_name: str, target_file_path: str) -> None:
        """从OCI对象存储下载文件并保存到本地路径"""

        client = self._get_client()
        bucket_namespace = self._get_oci_bucket_namespace()
        bucket_name = self._get_oci_bucket_name()

        try:
            # 从OCI获取对象
            get_object_response = client.get_object(
                namespace_name=bucket_namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )

            # 确保目标目录存在
            target_dir = os.path.dirname(target_file_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            # 从响应流中读取数据并写入目标文件
            with open(target_file_path, 'wb') as f:
                for chunk in get_object_response.data.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                raise FailException(f"文件不存在: {object_name}")
            raise FailException(f"下载文件失败: {str(e)}")
        except IOError as e:
            raise FailException(f"保存文件失败: {str(e)}")
        except Exception as e:
            raise FailException(f"下载文件时发生未知错误: {str(e)}")

    @classmethod
    def get_file_url(cls, object_name: str) -> str:
        """获取OCI对象的URL地址"""

        config = oci.config.from_file()

        bucket_namespace = cls._get_oci_bucket_namespace()
        bucket_name = cls._get_oci_bucket_name()
        region = config["region"]

        return f"https://{bucket_namespace}.objectstorage.{region}.oci.customer-oci.com/n/{bucket_namespace}/b/{bucket_name}/o/{object_name}"

    @classmethod
    def _get_client(cls) -> ObjectStorageClient:
        """获取OCI对象存储客户端"""

        config = oci.config.from_file()
        object_storage_client = oci.object_storage.ObjectStorageClient(config)
        return object_storage_client

    @classmethod
    def _get_oci_bucket_namespace(cls) -> str:
        """获取OCI存储桶的命名空间"""

        return os.environ.get("OCI_BUCKET_NAMESPACE")

    @classmethod
    def _get_oci_bucket_name(cls) -> str:
        """获取OCI存储桶的名称"""

        return os.environ.get("OCI_BUCKET_NAME")
