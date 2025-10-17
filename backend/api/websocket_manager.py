"""
WebSocket 连接管理器

管理 WebSocket 客户端连接和消息广播
"""

import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from logger import get_logger

logger = get_logger("websocket_manager")


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        # 活跃连接：client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # 订阅主题：topic -> Set[client_id]
        self.subscriptions: Dict[str, Set[str]] = {}

        # 锁
        self._lock = asyncio.Lock()

        logger.info("ConnectionManager 已初始化")

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        接受新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            client_id: 客户端唯一标识
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections[client_id] = websocket

        logger.info(f"客户端连接: {client_id}, 当前连接数: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        """
        断开 WebSocket 连接

        Args:
            client_id: 客户端唯一标识
        """
        async with self._lock:
            # 移除连接
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            # 移除所有订阅
            for topic in self.subscriptions:
                if client_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(client_id)

            # 清理空的订阅集合
            empty_topics = [topic for topic, clients in self.subscriptions.items() if not clients]
            for topic in empty_topics:
                del self.subscriptions[topic]

        logger.info(f"客户端断开: {client_id}, 当前连接数: {len(self.active_connections)}")

    async def subscribe(self, client_id: str, topic: str):
        """
        订阅主题

        Args:
            client_id: 客户端唯一标识
            topic: 主题名称
        """
        async with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()

            self.subscriptions[topic].add(client_id)

        logger.debug(f"客户端 {client_id} 订阅主题: {topic}")

    async def unsubscribe(self, client_id: str, topic: str):
        """
        取消订阅主题

        Args:
            client_id: 客户端唯一标识
            topic: 主题名称
        """
        async with self._lock:
            if topic in self.subscriptions and client_id in self.subscriptions[topic]:
                self.subscriptions[topic].remove(client_id)

                # 清理空的订阅集合
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]

        logger.debug(f"客户端 {client_id} 取消订阅主题: {topic}")

    async def send_personal_message(self, message: dict, client_id: str):
        """
        发送消息给特定客户端

        Args:
            message: 消息内容
            client_id: 客户端唯一标识
        """
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {client_id}, error={e}")
                await self.disconnect(client_id)

    async def broadcast(self, message: dict, topic: Optional[str] = None):
        """
        广播消息

        Args:
            message: 消息内容
            topic: 主题（None 表示广播给所有客户端）
        """
        # 添加时间戳
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # 确定接收者
        if topic is None:
            # 广播给所有客户端
            client_ids = list(self.active_connections.keys())
        else:
            # 广播给订阅了该主题的客户端
            client_ids = list(self.subscriptions.get(topic, set()))

        if not client_ids:
            return

        logger.debug(f"广播消息: topic={topic}, clients={len(client_ids)}")

        # 并发发送
        tasks = []
        for client_id in client_ids:
            websocket = self.active_connections.get(client_id)
            if websocket:
                tasks.append(self._send_with_error_handling(websocket, client_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_with_error_handling(
        self, websocket: WebSocket, client_id: str, message: dict
    ):
        """
        发送消息（带错误处理）

        Args:
            websocket: WebSocket 连接
            client_id: 客户端 ID
            message: 消息内容
        """
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            logger.warning(f"客户端已断开: {client_id}")
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"发送消息异常: {client_id}, error={e}")
            await self.disconnect(client_id)

    def get_client_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)

    def get_subscriptions_info(self) -> dict:
        """获取订阅信息"""
        return {
            topic: len(clients)
            for topic, clients in self.subscriptions.items()
        }

    async def send_heartbeat(self):
        """发送心跳消息给所有客户端"""
        message = {
            "type": "heartbeat",
            "data": {"timestamp": datetime.now().isoformat()},
        }
        await self.broadcast(message)


# 全局连接管理器实例
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    获取全局连接管理器实例

    Returns:
        ConnectionManager 实例
    """
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = ConnectionManager()

    return _connection_manager


async def start_heartbeat_task(interval: int = 30):
    """
    启动心跳任务

    Args:
        interval: 心跳间隔（秒）
    """
    manager = get_connection_manager()

    while True:
        try:
            await asyncio.sleep(interval)
            if manager.get_client_count() > 0:
                await manager.send_heartbeat()
                logger.debug(f"发送心跳: {manager.get_client_count()} 个客户端")
        except Exception as e:
            logger.error(f"心跳任务错误: {e}")


__all__ = [
    "ConnectionManager",
    "get_connection_manager",
    "start_heartbeat_task",
]
