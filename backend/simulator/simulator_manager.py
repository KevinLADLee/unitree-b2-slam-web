"""
仿真管理器

整合里程计模拟器和Notice模拟器，提供完整的仿真环境
"""

import asyncio
from typing import Optional

from simulator.odometry_simulator import OdometrySimulator
from simulator.notice_simulator import NoticeSimulator
from slam.message_types import QtCommand_, QtNode_, QtEdge_, Odometry_, String_
from logger import get_logger

logger = get_logger("simulator_manager")


class SimulatorManager:
    """仿真管理器"""

    def __init__(
        self,
        odom_rate: float = 10.0,
        odom_noise: float = 0.01,
        notice_delay: float = 0.5,
    ):
        """
        初始化仿真管理器

        Args:
            odom_rate: 里程计发布频率（Hz）
            odom_noise: 里程计噪声级别
            notice_delay: Notice 响应延迟（秒）
        """
        # 创建模拟器
        self.odom_sim = OdometrySimulator(
            publish_rate=odom_rate,
            noise_level=odom_noise,
        )

        self.notice_sim = NoticeSimulator(
            response_delay=notice_delay,
        )

        # 回调函数（由外部设置）
        self._odom_callback: Optional[callable] = None
        self._notice_callback: Optional[callable] = None

        logger.info(
            f"SimulatorManager 初始化: "
            f"odom_rate={odom_rate}Hz, "
            f"notice_delay={notice_delay}s"
        )

    def set_odom_callback(self, callback: callable):
        """
        设置里程计回调

        Args:
            callback: 回调函数 (Odometry_) -> None
        """
        self._odom_callback = callback
        self.odom_sim.set_callback(callback)
        logger.debug("里程计回调已设置")

    def set_notice_callback(self, callback: callable):
        """
        设置 Notice 回调

        Args:
            callback: 回调函数 (String_) -> None
        """
        self._notice_callback = callback
        self.notice_sim.set_callback(callback)
        logger.debug("Notice 回调已设置")

    async def start(self):
        """启动仿真"""
        await self.odom_sim.start()
        logger.info("仿真管理器已启动")

    async def stop(self):
        """停止仿真"""
        await self.odom_sim.stop()
        logger.info("仿真管理器已停止")

    async def handle_command(self, cmd: QtCommand_):
        """
        处理命令

        Args:
            cmd: Qt 命令
        """
        await self.notice_sim.handle_command(cmd)

    async def handle_save_nodes(self, qt_node: QtNode_):
        """
        处理保存节点

        Args:
            qt_node: Qt 节点消息
        """
        await self.notice_sim.handle_save_nodes(qt_node)

    async def handle_save_edges(self, qt_edge: QtEdge_):
        """
        处理保存边

        Args:
            qt_edge: Qt 边消息
        """
        await self.notice_sim.handle_save_edges(qt_edge)

    def get_current_pose(self) -> tuple[float, float, float, float]:
        """
        获取当前位姿

        Returns:
            (x, y, z, yaw)
        """
        return self.odom_sim.get_current_pose()

    def set_robot_pose(self, x: float, y: float, z: float, yaw: float):
        """
        设置机器人位姿

        Args:
            x, y, z: 位置
            yaw: 角度
        """
        self.odom_sim.set_pose(x, y, z, yaw)

    def move_robot_to(self, target_x: float, target_y: float, speed: float = 0.5):
        """
        移动机器人到指定位置

        Args:
            target_x: 目标 X
            target_y: 目标 Y
            speed: 速度
        """
        self.odom_sim.move_to_point(target_x, target_y, speed)

    def is_robot_at(self, target_x: float, target_y: float, tolerance: float = 0.1) -> bool:
        """
        检查机器人是否到达指定位置

        Args:
            target_x: 目标 X
            target_y: 目标 Y
            tolerance: 容差

        Returns:
            是否到达
        """
        return self.odom_sim.is_at_point(target_x, target_y, tolerance)

    def get_saved_topology(self) -> dict:
        """
        获取已保存的拓扑图

        Returns:
            拓扑图数据
        """
        return {
            "nodes": dict(self.notice_sim.nodes),
            "edges": dict(self.notice_sim.edges),
        }


# 全局仿真管理器实例
_simulator_manager: Optional[SimulatorManager] = None


def get_simulator_manager() -> SimulatorManager:
    """
    获取全局仿真管理器实例

    Returns:
        SimulatorManager 实例
    """
    global _simulator_manager

    if _simulator_manager is None:
        _simulator_manager = SimulatorManager()

    return _simulator_manager


def initialize_simulator_manager(
    odom_rate: float = 10.0,
    odom_noise: float = 0.01,
    notice_delay: float = 0.5,
) -> SimulatorManager:
    """
    初始化全局仿真管理器

    Args:
        odom_rate: 里程计频率
        odom_noise: 里程计噪声
        notice_delay: Notice 延迟

    Returns:
        SimulatorManager 实例
    """
    global _simulator_manager

    if _simulator_manager is not None:
        logger.warning("SimulatorManager 已初始化，将重新创建")

    _simulator_manager = SimulatorManager(odom_rate, odom_noise, notice_delay)

    return _simulator_manager


__all__ = [
    "SimulatorManager",
    "get_simulator_manager",
    "initialize_simulator_manager",
]
