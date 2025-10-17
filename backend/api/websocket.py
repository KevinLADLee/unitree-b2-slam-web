"""
WebSocket API

提供实时数据推送的 WebSocket 接口
"""

import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional

from api.websocket_manager import get_connection_manager, ConnectionManager
from api.dependencies import SlamServiceDep
from slam.message_types import QtNotice, Odometry_
from logger import get_logger

logger = get_logger("api.websocket")

router = APIRouter(tags=["WebSocket"])


# WebSocket 主题定义
TOPIC_QT_NOTICE = "qt_notice"           # Qt Notice 消息
TOPIC_ODOMETRY = "odometry"             # 里程计数据
TOPIC_SYSTEM_STATUS = "system_status"   # 系统状态
TOPIC_NAV_FEEDBACK = "nav_feedback"     # 导航反馈


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    slam_service: SlamServiceDep,
):
    """
    WebSocket 主端点

    连接后可以接收：
    - qt_notice: SLAM 系统通知
    - odometry: 里程计数据
    - system_status: 系统状态更新
    - nav_feedback: 导航反馈

    发送消息格式：
    {
        "action": "subscribe" | "unsubscribe",
        "topic": "qt_notice" | "odometry" | "system_status" | "nav_feedback"
    }
    """
    # 生成客户端 ID
    client_id = str(uuid.uuid4())

    # 获取连接管理器
    manager = get_connection_manager()

    # 接受连接
    await manager.connect(websocket, client_id)

    # 注册 SLAM 服务回调
    _register_slam_callbacks(slam_service, manager)

    # 发送欢迎消息
    await manager.send_personal_message(
        {
            "type": "connected",
            "data": {
                "client_id": client_id,
                "message": "WebSocket 连接成功",
                "available_topics": [
                    TOPIC_QT_NOTICE,
                    TOPIC_ODOMETRY,
                    TOPIC_SYSTEM_STATUS,
                    TOPIC_NAV_FEEDBACK,
                ],
            },
        },
        client_id,
    )

    try:
        # 处理客户端消息
        while True:
            # 接收消息
            data = await websocket.receive_json()

            action = data.get("action")
            topic = data.get("topic")

            if action == "subscribe" and topic:
                await manager.subscribe(client_id, topic)
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "data": {"topic": topic, "message": f"已订阅 {topic}"},
                    },
                    client_id,
                )

            elif action == "unsubscribe" and topic:
                await manager.unsubscribe(client_id, topic)
                await manager.send_personal_message(
                    {
                        "type": "unsubscribed",
                        "data": {"topic": topic, "message": f"已取消订阅 {topic}"},
                    },
                    client_id,
                )

            elif action == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "data": {}},
                    client_id,
                )

            else:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "data": {"message": f"未知操作: {action}"},
                    },
                    client_id,
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端主动断开: {client_id}")
        await manager.disconnect(client_id)

    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        await manager.disconnect(client_id)


def _register_slam_callbacks(slam_service, manager: ConnectionManager):
    """
    注册 SLAM 服务回调

    Args:
        slam_service: SLAM 服务实例
        manager: 连接管理器
    """
    # 检查回调是否已注册（避免重复注册）
    if hasattr(_register_slam_callbacks, "_registered"):
        return

    _register_slam_callbacks._registered = True

    # Qt Notice 回调
    def on_qt_notice(qt_notice: QtNotice):
        """处理 qt_notice 消息"""
        try:
            # 构建消息
            message = {
                "type": "qt_notice",
                "data": {
                    "index": qt_notice.index,
                    "notice": qt_notice.notice,
                    "feedback": qt_notice.feedback,
                    "state": qt_notice.state,
                    "arrive": qt_notice.arrive,
                    "finish": qt_notice.finish,
                    "all": qt_notice.all,
                    "loop": qt_notice.loop,
                    "obstruct": qt_notice.obstruct,
                },
            }

            # 区分命令反馈和导航反馈
            if qt_notice.index <= 10000:
                # 命令反馈
                asyncio.create_task(manager.broadcast(message, TOPIC_QT_NOTICE))
            else:
                # 导航反馈
                asyncio.create_task(manager.broadcast(message, TOPIC_NAV_FEEDBACK))

        except Exception as e:
            logger.error(f"处理 qt_notice 回调失败: {e}")

    # 里程计回调
    def on_odometry(odom: Odometry_):
        """处理里程计数据"""
        try:
            pose = odom.pose.pose
            message = {
                "type": "odometry",
                "data": {
                    "position": {
                        "x": pose.position.x,
                        "y": pose.position.y,
                        "z": pose.position.z,
                    },
                    "orientation": {
                        "qx": pose.orientation.x,
                        "qy": pose.orientation.y,
                        "qz": pose.orientation.z,
                        "qw": pose.orientation.w,
                    },
                },
            }

            asyncio.create_task(manager.broadcast(message, TOPIC_ODOMETRY))

        except Exception as e:
            logger.error(f"处理里程计回调失败: {e}")

    # 注册回调
    slam_service.register_notice_callback(on_qt_notice)
    slam_service.register_odom_callback(on_odometry)

    logger.info("SLAM 服务回调已注册到 WebSocket")


@router.get("/ws/info")
async def websocket_info():
    """
    获取 WebSocket 信息

    Returns:
        WebSocket 连接信息
    """
    manager = get_connection_manager()

    return {
        "endpoint": "/ws",
        "protocol": "ws",
        "client_count": manager.get_client_count(),
        "subscriptions": manager.get_subscriptions_info(),
        "available_topics": [
            {
                "topic": TOPIC_QT_NOTICE,
                "description": "SLAM 系统通知和命令反馈",
            },
            {
                "topic": TOPIC_ODOMETRY,
                "description": "机器人里程计数据",
            },
            {
                "topic": TOPIC_SYSTEM_STATUS,
                "description": "系统状态更新",
            },
            {
                "topic": TOPIC_NAV_FEEDBACK,
                "description": "导航过程反馈",
            },
        ],
    }


__all__ = ["router"]
