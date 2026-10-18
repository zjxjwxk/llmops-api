#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/2/25 21:16
@File   :   app_service.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from flask import request
from injector import inject
from sqlalchemy import func, desc

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.exception import NotFoundException, ForbiddenException, ValidationException, FailException
from internal.lib.helper import datetime_to_timestamp
from internal.model import App, Account, AppConfigVersion, ApiTool, Dataset, AppConfig, AppDataset
from internal.schema.app_schema import CreateAppReq, GetPublishHistoriesWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""

    db: SQLAlchemy
    builtin_provider_manager: BuiltinProviderManager

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """创建应用"""

        with self.db.auto_commit():
            # 1. 创建应用记录
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 创建应用配置草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 更新应用草稿配置ID
            app.draft_app_config_id = app_config_version.id

        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """获取应用信息"""

        # 获取应用信息
        app = self.get(App, app_id)

        # 判断应用是否存在
        if not app:
            raise NotFoundException("该应用不存在，请核实后重试")

        # 判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后重试")

        return app

    def get_draft_app_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """获取应用草稿配置"""

        # 获取应用草稿配置
        app = self.get_app(app_id, account)
        draft_app_config = app.draft_app_config

        # TODO: 校验model_config配置，待实现多模型后补充

        # 校验工具列表
        draft_tools = draft_app_config.tools
        validated_tools = []
        tools = []

        for draft_tool in draft_tools:
            if draft_tool["type"] == "builtin_tool":
                # 检查内置工具提供商是否存在
                provider = self.builtin_provider_manager.get_provider(draft_tool["provider_id"])
                if not provider:
                    continue

                # 检查内置工具是否存在
                tool_entity = provider.get_tool_entity(draft_tool["tool_id"])
                if not tool_entity:
                    continue

                # 校验工具参数是否一致，若不一致则重置为默认值
                param_keys = set([param.name for param in tool_entity.params])
                params = draft_tool["params"]
                if set(draft_tool["params"].keys()) - param_keys:
                    params = {
                        param.name: param.default
                        for param in tool_entity.params if param.default is not None
                    }

                # 校验通过，则加入已校验工具列表
                validated_tools.append({**draft_tool, "params": params})

                # 封装工具响应结构
                provider_entity = provider.provider_entity
                tools.append({
                    "type": "builtin_tool",
                    "provider": {
                        "id": provider_entity.name,
                        "name": provider_entity.name,
                        "label": provider_entity.label,
                        "icon": f"{request.scheme}://{request.host}/builtin-tools/{provider_entity.name}/icon",
                        "description": provider_entity.description,
                    },
                    "tool": {
                        "id": tool_entity.name,
                        "name": tool_entity.name,
                        "label": tool_entity.label,
                        "description": tool_entity.description,
                        "params": draft_tool["params"],
                    }
                })
            elif draft_tool["type"] == "api_tool":
                # 检查自定义工具是否存在
                tool_record = self.db.session.query(ApiTool).filter(
                    ApiTool.provider_id == draft_tool["provider_id"],
                    ApiTool.name == draft_tool["tool_id"],
                ).one_or_none()
                if not tool_record:
                    continue

                # 校验通过，则加入已校验工具列表
                validated_tools.append(draft_tool)

                # 封装工具响应结构
                provider = tool_record.provider
                tools.append({
                    "type": "api_tool",
                    "provider": {
                        "id": str(provider.id),
                        "name": provider.name,
                        "label": provider.name,
                        "icon": provider.icon,
                        "description": provider.description,
                    },
                    "tool": {
                        "id": str(tool_record.id),
                        "name": tool_record.name,
                        "label": tool_record.name,
                        "description": tool_record.description,
                        "params": {},
                    }
                })

        # 更新草稿配置中的工具列表为已校验工具列表
        if draft_tools != validated_tools:
            self.update(draft_app_config, tools=validated_tools)

        # 校验知识库列表
        draft_datasets = draft_app_config.datasets
        datasets = []

        dataset_records = self.db.session.query(Dataset).filter(Dataset.id.in_(draft_datasets)).all()
        dataset_dict = {str(dataset_record.id): dataset_record for dataset_record in dataset_records}
        dataset_sets = set(dataset_dict.keys())

        # 过滤出存在的知识库列表（按照原草稿列表顺序）
        exist_dataset_ids = [dataset_id for dataset_id in draft_datasets if dataset_id in dataset_sets]

        # 更新草稿配置中的知识库列表为存在的知识库列表
        if set(exist_dataset_ids) != set(draft_datasets):
            self.update(draft_app_config, datasets=exist_dataset_ids)

        # 封装知识库列表响应结构
        for dataset_id in exist_dataset_ids:
            dataset = dataset_dict.get(str(dataset_id))
            datasets.append({
                "id": str(dataset.id),
                "name": dataset.name,
                "icon": dataset.icon,
                "description": dataset.description,
            })

        # TODO: 校验工作流列表
        workflows = []

        return {
            "id": str(draft_app_config.id),
            "model_config": draft_app_config.model_config,
            "dialog_round": draft_app_config.dialog_round,
            "preset_prompt": draft_app_config.preset_prompt,
            "tools": tools,
            "workflows": workflows,
            "datasets": datasets,
            "retrieval_config": draft_app_config.retrieval_config,
            "long_term_memory": draft_app_config.long_term_memory,
            "opening_statement": draft_app_config.opening_statement,
            "opening_questions": draft_app_config.opening_questions,
            "speech_to_text": draft_app_config.speech_to_text,
            "text_to_speech": draft_app_config.text_to_speech,
            "review_config": draft_app_config.review_config,
            "updated_at": datetime_to_timestamp(draft_app_config.updated_at),
            "created_at": datetime_to_timestamp(draft_app_config.created_at),
        }

    def get_publish_histories_with_page(
            self,
            app_id: UUID,
            req: GetPublishHistoriesWithPageReq,
            account: Account
    ) -> tuple[list[AppConfigVersion], Paginator]:
        """获取应用发布历史列表分页"""

        # 获取应用信息（校验用户权限）
        self.get_app(app_id, account)

        # 构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 分页获取数据
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion).filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            ).order_by(desc("version"))
        )

        return app_config_versions, paginator

    def update_draft_app_config(
            self,
            app_id: UUID,
            draft_app_config:
            dict[str, Any],
            account: Account
    ) -> AppConfigVersion:
        """更新应用草稿配置"""

        # 获取应用信息（并校验权限）
        app = self.get_app(app_id, account)

        # 校验传入应用草稿配置
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)

        # 获取最新应用草稿配置
        draft_app_config_record = app.draft_app_config

        self.update(
            draft_app_config_record,
            # TODO: 由于目前model使用server_onupdate，需暂时手动设置更新时间
            updated_at=datetime.now(),
            **draft_app_config,
        )

        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account) -> App:
        """发布应用配置"""

        # 获取应用信息（并校验权限）
        app = self.get_app(app_id, account)

        # 获取应用草稿配置
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 创建应用运行配置
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=draft_app_config["model_config"],
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],
            # TODO: 待工作流模块后更新
            workflows=draft_app_config["workflows"],
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            review_config=draft_app_config["review_config"],
        )

        # 更新应用关联的运行配置及应用状态
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 删除原有知识库关联记录
        with self.db.auto_commit():
            self.db.session.query(AppDataset).filter(
                AppDataset.app_id == app_id
            ).delete()

        # 创建新的知识库关联记录
        for dataset in draft_app_config["datasets"]:
            self.create(AppDataset, app_id=app_id, dataset_id=dataset["id"])

        # 获取应用草稿配置，并去除草稿相关字段
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields = ["id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"]
        for field in remove_fields:
            draft_app_config_copy.pop(field)

        # 获取当前最新发布版本
        max_version = self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0)).filter(
            AppConfigVersion.app_id == app_id,
            AppConfigVersion.config_type == AppConfigType.PUBLISHED,
        ).scalar()

        # 创建应用发布历史配置
        self.create(
            AppConfigVersion,
            version=max_version + 1,
            config_type=AppConfigType.PUBLISHED,
            **draft_app_config_copy,
        )

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account) -> App:
        """取消发布应用配置"""

        # 获取应用信息（并校验权限）
        app = self.get_app(app_id, account)

        if app.status != AppStatus.PUBLISHED:
            raise FailException("当前应用未发布，请核实后重试")

        # 更新应用发布状态，并清空应用关联配置ID
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 删除应用关联的知识库信息
        with self.db.auto_commit():
            self.db.session.query(AppDataset).filter(
                AppDataset.app_id == app_id
            ).delete()

        return app

    def fallback_history_to_draft(self, app_id: UUID, app_config_version_id: UUID,
                                  account: Account) -> AppConfigVersion:
        """回退应用历史配置到草稿"""

        # 获取应用信息（并校验权限）
        app = self.get_app(app_id, account)

        # 获取应用历史版本配置
        app_config_version = self.get(AppConfigVersion, app_config_version_id)
        if not app_config_version:
            raise NotFoundException("该应用历史版本配置不存在，请核实后重试")

        # 拷贝历史配置为草稿配置，并去除特定字段
        draft_app_config_dict = app_config_version.__dict__.copy()
        remove_fields = ["id", "app_id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"]
        for field in remove_fields:
            draft_app_config_dict.pop(field)

        # 校验草稿配置
        draft_app_config_dict = self._validate_draft_app_config(draft_app_config_dict, account)

        # 更新草稿配置
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            # TODO: 由于目前model使用server_onupdate，需暂时手动设置更新时间
            updated_at=datetime.now(),
            **draft_app_config_dict,
        )

        return draft_app_config_record

    def _validate_draft_app_config(self, draft_app_config: dict[str, Any], account: Account) -> dict[str, Any]:
        """校验应用草稿配置"""

        # 校验草稿配置字段
        acceptable_fields = [
            "model_config", "dialog_round", "preset_prompt",
            "tools", "workflows", "datasets", "retrieval_config",
            "long_term_memory", "opening_statement", "opening_questions",
            "speech_to_text", "text_to_speech", "review_config"
        ]

        if (
                not draft_app_config
                or not isinstance(draft_app_config, dict)
                or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidationException("草稿配置字段错误，请核实后重试")

        # TODO: 校验model_config字段，待实现多模型后补充

        # 校验携带对话轮数
        if "dialog_round" in draft_app_config:
            dialog_round = draft_app_config["dialog_round"]
            if (
                    not isinstance(dialog_round, int)
                    or not (0 <= dialog_round <= 100)
            ):
                raise ValidationException("携带对话轮数范围必须在0~100之间")

        # 校验预设提示词
        if "preset_prompt" in draft_app_config:
            preset_prompt = draft_app_config["preset_prompt"]
            if (
                    not isinstance(preset_prompt, str)
                    or len(preset_prompt) > 2000
            ):
                raise ValidationException("人设与回复逻辑必须为字符串，长度在0~2000个字符之间")

        # 校验工具列表
        if "tools" in draft_app_config:
            tools = draft_app_config["tools"]
            validated_tools = []

            if not isinstance(tools, list):
                raise ValidationException("工具列表必须为列表类型")

            if len(tools) > 5:
                raise ValidationException("工具列表数量不能超过5个")

            for tool in tools:
                # 校验工具参数
                if not tool or not isinstance(tool, dict):
                    raise ValidationException("工具列表中的工具必须为字典类型")

                if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                    raise ValidationException("工具参数名称错误")

                if tool["type"] not in ["builtin_tool", "api_tool"]:
                    raise ValidationException("工具类型不支持")

                if (
                        not tool["provider_id"]
                        or not tool["tool_id"]
                        or not isinstance(tool["provider_id"], str)
                        or not isinstance(tool["tool_id"], str)
                ):
                    raise ValidationException("工具提供商或标识不能为空且必须为字符串类型")

                if not isinstance(tool["params"], dict):
                    raise ValidationException("工具自定义参数必须为字典类型")

                # 校验工具是否存在
                if tool["type"] == "builtin_tool":
                    builtin_tool = self.builtin_provider_manager.get_tool(tool["provider_id"], tool["tool_id"])
                    if not builtin_tool:
                        continue
                else:
                    api_tool = self.db.session.query(ApiTool).filter(
                        ApiTool.provider_id == tool["provider_id"],
                        ApiTool.name == tool["tool_id"],
                        ApiTool.account_id == account.id,
                    )
                    if not api_tool:
                        continue

                validated_tools.append(tool)

            # 校验工具是否重复
            unique_tool_ids = [f"{tool['provider_id']}_{tool['tool_id']}" for tool in validated_tools]
            if len(unique_tool_ids) != len(validated_tools):
                raise ValidationException("存在重复绑定的工具")

            draft_app_config["tools"] = validated_tools

        # TODO: 校验工作流列表
        if "workflows" in draft_app_config:
            draft_app_config["workflows"] = []

        # 校验知识库列表
        if "datasets" in draft_app_config:
            datasets = draft_app_config["datasets"]

            if not isinstance(datasets, list):
                raise ValidationException("知识库列表必须为列表类型")

            if len(datasets) > 5:
                raise ValidationException("知识库列表数量不能超过5个")

            for dataset_id in datasets:
                # 校验知识库参数
                try:
                    UUID(dataset_id)
                except Exception:
                    raise ValidationException("知识库列表参数必须为UUID类型")

            # 校验知识库是否重复
            if len(set(datasets)) != len(datasets):
                raise ValidationException("存在重复绑定的知识库")

            # 校验知识库权限，去除不属于当前账号的知识库
            dataset_records = self.db.session.query(Dataset).filter(
                Dataset.id.in_(datasets),
                Dataset.account_id == account.id,
            ).all()
            dataset_sets = set([str(dataset_record.id) for dataset_record in dataset_records])
            draft_app_config["datasets"] = [dataset_id for dataset_id in datasets if dataset_id in dataset_sets]

        # 校验检索配置
        if "retrieval_config" in draft_app_config:
            retrieval_config = draft_app_config["retrieval_config"]

            # 校验检索配置参数
            if not retrieval_config or not isinstance(retrieval_config, dict):
                raise ValidationException("检索配置不能为空且必须为字典类型")

            if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
                raise ValidationException("检索配置参数名称错误")

            if retrieval_config["retrieval_strategy"] not in ["semantic", "full_text", "hybrid"]:
                raise ValidationException("检索策略类型不支持")

            if not isinstance(retrieval_config["k"], int) or not (0 <= retrieval_config["k"] <= 10):
                raise ValidationException("最大召回数量必须为整数类型，且范围必须在0~10之间")

            if not isinstance(retrieval_config["score"], float) or not (0 <= retrieval_config["score"] <= 1):
                raise ValidationException("最小匹配度必须为浮点数类型，且范围必须在0~1之间")

        # 校验长期记忆
        if "long_term_memory" in draft_app_config:
            long_term_memory = draft_app_config["long_term_memory"]

            if not long_term_memory or not isinstance(long_term_memory, dict):
                raise ValidationException("长期记忆不能为空，且必须为字典类型")

            if (
                    set(long_term_memory.keys()) != {"enable"}
                    or not isinstance(long_term_memory["enable"], bool)
            ):
                raise ValidationException("长期记忆参数名称错误，或参数值类型错误")

        # 校验对话开场白
        if "opening_statement" in draft_app_config:
            opening_statement = draft_app_config["opening_statement"]

            if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
                raise ValidationException("对话开场白必须为字符串类型，且长度不能超过2000")

        # 校验对话开场建议问题列表
        if "opening_questions" in draft_app_config:
            opening_questions = draft_app_config["opening_questions"]

            if not isinstance(opening_questions, list) or len(opening_questions) > 3:
                raise ValidationException("对话开场建议问题列表必须为列表类型，且数量不能超过3个")

            for opening_question in opening_questions:
                if not isinstance(opening_question, str):
                    raise ValidationException("对话开场建议问题列表中的问题必须为字符串类型")

        # 校验语音转文本配置
        if "speech_to_text" in draft_app_config:
            speech_to_text = draft_app_config["speech_to_text"]

            if not speech_to_text or not isinstance(speech_to_text, dict):
                raise ValidationException("语音转文本配置不能为空，且必须为字典类型")

            if (
                    set(speech_to_text.keys()) != {"enable"}
                    or not isinstance(speech_to_text["enable"], bool)
            ):
                raise ValidationException("语音转文本配置参数名称错误，或参数值类型错误")

        # 校验文本转语音配置
        if "text_to_speech" in draft_app_config:
            text_to_speech = draft_app_config["text_to_speech"]

            if not isinstance(text_to_speech, dict):
                raise ValidationException("文本转语音配置不能为空，且必须为字典类型")

            if (
                    set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                    or not isinstance(text_to_speech["enable"], bool)
                    # TODO: 校验音色参数，待实现多模态后
                    or text_to_speech["voice"] not in ["echo"]
                    or not isinstance(text_to_speech["auto_play"], bool)
            ):
                raise ValidationException("文本转语音配置参数名称错误，或参数值类型错误")

        # 校验审核配置
        if "review_config" in draft_app_config:
            review_config = draft_app_config["review_config"]

            # 校验审核参数
            if not review_config or not isinstance(review_config, dict):
                raise ValidationException("审核配置不能为空，且必须为字典类型")

            if set(review_config.keys()) != {"enable", "keywords", "inputs_config", "outputs_config"}:
                raise ValidationException("审核配置参数名称错误")

            if not isinstance(review_config["enable"], bool):
                raise ValidationException("审核配置中启用状态必须为布尔类型")

            # 校验敏感词列表
            if (
                    not isinstance(review_config["keywords"], list)
                    or (review_config["enable"] and len(review_config["keywords"]) == 0)
                    or len(review_config["keywords"]) > 100
            ):
                raise ValidationException(
                    "审核配置中敏感词列表必须为列表类型；当启用审核时，列表不能为空；数量不能超过100个")

            for keyword in review_config["keywords"]:
                if not isinstance(keyword, str):
                    raise ValidationException("审核配置的敏感词列表中的敏感词必须为字符串类型")

            # 校验输入审核配置
            if not review_config["inputs_config"] or not isinstance(review_config["inputs_config"], dict):
                raise ValidationException("审核配置中输入审核配置不能为空，且必须为字典类型")

            if (
                    set(review_config["inputs_config"]) != {"enable", "preset_response"}
                    or not isinstance(review_config["inputs_config"]["enable"], bool)
                    or not isinstance(review_config["inputs_config"]["preset_response"], str)
            ):
                raise ValidationException("审核配置中输入审核配置参数名称错误，或参数值类型错误")

            # 校验输出审核配置
            if not review_config["outputs_config"] or not isinstance(review_config["outputs_config"], dict):
                raise ValidationException("审核配置中输出审核配置不能为空，且必须为字典类型")

            if (
                    set(review_config["outputs_config"]) != {"enable"}
                    or not isinstance(review_config["outputs_config"]["enable"], bool)
            ):
                raise ValidationException("审核配置中输出审核配置参数名称错误，或参数值类型错误")

            # 校验输入审核或输出审核配置是否开启
            if review_config["enable"]:
                if (
                        review_config["inputs_config"]["enable"] is False
                        and review_config["outputs_config"]["enable"] is False
                ):
                    raise ValidationException("输入审核或输出审核至少至少开启一项")

                if (
                        review_config["inputs_config"]["enable"]
                        and review_config["inputs_config"]["preset_response"].strip() == ""
                ):
                    raise ValidationException("输入审核的预设响应不能为空")

        return draft_app_config
