#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author :   Xinkang Wu
@Time   :   2026/8/29 16:47
@File   :   agent_queue_manager.py
"""
import queue
import time
import uuid
from queue import Queue
from typing import Generator
from uuid import UUID

from redis import Redis

from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    """Agent事件队列管理器"""

    user_id: UUID
    invoke_from: InvokeFrom
    redis_client: Redis
    _queues: dict[str, Queue]

    def __init__(
            self,
            user_id: UUID,
            invoke_from: InvokeFrom,
    ) -> None:
        """构造函数"""

        # 初始化
        self.user_id = user_id
        self.invoke_from = invoke_from
        self._queues = {}

        from app.http.module import injector
        self.redis_client = injector.get(Redis)

    def listen(self, task_id: UUID) -> Generator:
        """监听队列返回的流式数据"""

        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        # 死循环获取队列数据
        while True:
            try:
                # 获取队列中的事件并返回
                item = self.get_queue(task_id).get(timeout=1)
                if item is None:
                    break
                yield item
            except queue.Empty:
                # 队列为空，继续尝试获取
                continue
            finally:
                # 每次获取事件后

                # 更新总耗时
                elapsed_time = time.time() - start_time

                # 每10秒发起一个PING请求事件
                if elapsed_time // 10 > last_ping_time:
                    # 添加PING连通事件
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.PING
                    ))
                    last_ping_time = elapsed_time // 10

                # 判断总耗时是否超时
                if elapsed_time >= listen_timeout:
                    # 添加超时事件
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.TIMEOUT
                    ))

                # 判断是否停止
                if self._is_stopped(task_id):
                    # 添加停止事件
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.STOP
                    ))

    def publish(self, task_id: UUID, agent_thought: AgentThought):
        """发布事件至队列"""

        self.get_queue(task_id).put(agent_thought)

        # 判断是否为停止事件
        if agent_thought.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT, QueueEvent.AGENT_END]:
            self.stop_listen(task_id)

    def stop_listen(self, task_id: UUID) -> None:
        """停止监听队列"""

        self.get_queue(task_id).put(None)

    def publish_error(self, task_id: UUID, error) -> None:
        """发布错误事件至队列"""

        self.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation=str(error)
        ))

    def get_queue(self, task_id: UUID):
        """获取Agent队列"""

        q = self._queues.get(str(task_id))

        if not q:
            # 根据用户类型生成缓存键
            user_prefix = "account" if self.invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER] else "end-user"

            # 添加任务缓存键标识，表示任务已启动
            self.redis_client.setex(
                self.generate_task_running_cache_key(task_id),
                1800,
                f"{user_prefix}-{str(self.user_id)}"
            )

            # 创建队列至字典
            q = Queue()
            self._queues[str(task_id)] = q

        return q

    def _is_stopped(self, task_id: UUID) -> bool:
        """判断任务是否停止"""

        task_stopped_cache_key = self.generate_task_stopped_cache_key(task_id)
        result = self.redis_client.get(task_stopped_cache_key)

        return result is not None

    @classmethod
    def generate_task_running_cache_key(cls, task_id: UUID) -> str:
        """生成任务已启动缓存键"""

        return f"generate_task_running:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: UUID) -> str:
        """生成任务已停止缓存键"""

        return f"generate_task_stopped:{str(task_id)}"
