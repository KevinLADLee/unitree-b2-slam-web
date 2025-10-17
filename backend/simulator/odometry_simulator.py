"""
里程计模拟器

在仿真模式下生成模拟的里程计数据
"""

import asyncio
import time
import math
from typing import Optional, Callable
from dataclasses import dataclass

from slam.message_types import Odometry_, PoseWithCovariance, Pose, Point, Quaternion
from logger import get_logger

logger = get_logger("odometry_simulator")


@dataclass
class RobotState:
    """机器人状态"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    vx: float = 0.0  # 线速度 x
    vy: float = 0.0  # 线速度 y
    omega: float = 0.0  # 角速度


class OdometrySimulator:
    """里程计模拟器"""

    def __init__(
        self,
        publish_rate: float = 10.0,
        noise_level: float = 0.01,
    ):
        """
        初始化里程计模拟器

        Args:
            publish_rate: 发布频率（Hz）
            noise_level: 噪声级别（0-1）
        """
        self.publish_rate = publish_rate
        self.noise_level = noise_level

        # 机器人状态
        self.state = RobotState()

        # 回调函数
        self._callback: Optional[Callable] = None

        # 运行标志
        self._running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(f"OdometrySimulator 初始化: rate={publish_rate}Hz, noise={noise_level}")

    def set_callback(self, callback: Callable[[Odometry_], None]):
        """
        设置里程计数据回调

        Args:
            callback: 回调函数
        """
        self._callback = callback
        logger.debug("里程计回调已设置")

    def set_velocity(self, vx: float, vy: float, omega: float):
        """
        设置机器人速度

        Args:
            vx: 线速度 x (m/s)
            vy: 线速度 y (m/s)
            omega: 角速度 (rad/s)
        """
        self.state.vx = vx
        self.state.vy = vy
        self.state.omega = omega
        logger.debug(f"设置速度: vx={vx:.2f}, vy={vy:.2f}, omega={omega:.2f}")

    def set_pose(self, x: float, y: float, z: float, yaw: float):
        """
        设置机器人位姿

        Args:
            x: X 坐标 (m)
            y: Y 坐标 (m)
            z: Z 坐标 (m)
            yaw: Yaw 角度 (rad)
        """
        self.state.x = x
        self.state.y = y
        self.state.z = z
        self.state.yaw = yaw
        logger.debug(f"设置位姿: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")

    def get_current_pose(self) -> tuple[float, float, float, float]:
        """
        获取当前位姿

        Returns:
            (x, y, z, yaw)
        """
        return self.state.x, self.state.y, self.state.z, self.state.yaw

    async def start(self):
        """启动里程计模拟"""
        if self._running:
            logger.warning("里程计模拟器已在运行")
            return

        self._running = True
        self._task = asyncio.create_task(self._publish_loop())
        logger.info("里程计模拟器已启动")

    async def stop(self):
        """停止里程计模拟"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("里程计模拟器已停止")

    async def _publish_loop(self):
        """发布循环"""
        dt = 1.0 / self.publish_rate

        try:
            while self._running:
                # 更新机器人状态
                self._update_state(dt)

                # 生成里程计消息
                odom = self._generate_odometry()

                # 触发回调
                if self._callback:
                    self._callback(odom)

                # 等待下一个周期
                await asyncio.sleep(dt)

        except asyncio.CancelledError:
            logger.debug("发布循环已取消")
            raise

    def _update_state(self, dt: float):
        """
        更新机器人状态

        Args:
            dt: 时间步长 (s)
        """
        # 添加噪声
        import random
        noise = lambda: random.uniform(-self.noise_level, self.noise_level)

        # 更新位置（考虑旋转）
        cos_yaw = math.cos(self.state.yaw)
        sin_yaw = math.sin(self.state.yaw)

        # 世界坐标系下的速度
        vx_world = self.state.vx * cos_yaw - self.state.vy * sin_yaw
        vy_world = self.state.vx * sin_yaw + self.state.vy * cos_yaw

        # 更新位置
        self.state.x += (vx_world + noise()) * dt
        self.state.y += (vy_world + noise()) * dt

        # 更新角度
        self.state.yaw += (self.state.omega + noise() * 0.1) * dt

        # 归一化角度到 [-pi, pi]
        self.state.yaw = math.atan2(math.sin(self.state.yaw), math.cos(self.state.yaw))

    def _generate_odometry(self) -> Odometry_:
        """
        生成里程计消息

        Returns:
            Odometry_ 消息
        """
        # 将 yaw 转换为四元数
        cy = math.cos(self.state.yaw * 0.5)
        sy = math.sin(self.state.yaw * 0.5)

        odom = Odometry_()
        odom.pose = PoseWithCovariance()
        odom.pose.pose = Pose()

        # 位置
        odom.pose.pose.position = Point(
            x=self.state.x,
            y=self.state.y,
            z=self.state.z,
        )

        # 方向（四元数）
        odom.pose.pose.orientation = Quaternion(
            x=0.0,
            y=0.0,
            z=sy,
            w=cy,
        )

        return odom

    def move_to_point(self, target_x: float, target_y: float, speed: float = 0.5):
        """
        移动到指定点（设置速度）

        Args:
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
            speed: 移动速度 (m/s)
        """
        # 计算方向
        dx = target_x - self.state.x
        dy = target_y - self.state.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.01:
            # 已到达
            self.set_velocity(0, 0, 0)
            return

        # 计算目标角度
        target_yaw = math.atan2(dy, dx)

        # 计算角度差
        yaw_diff = target_yaw - self.state.yaw
        yaw_diff = math.atan2(math.sin(yaw_diff), math.cos(yaw_diff))

        # 如果角度差太大，先旋转
        if abs(yaw_diff) > 0.1:
            omega = 1.0 if yaw_diff > 0 else -1.0
            self.set_velocity(0, 0, omega)
        else:
            # 向目标移动
            vx = speed
            omega = yaw_diff * 2.0  # 同时修正角度
            self.set_velocity(vx, 0, omega)

    def is_at_point(self, target_x: float, target_y: float, tolerance: float = 0.1) -> bool:
        """
        检查是否到达指定点

        Args:
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
            tolerance: 容差 (m)

        Returns:
            是否到达
        """
        dx = target_x - self.state.x
        dy = target_y - self.state.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < tolerance


__all__ = ["OdometrySimulator", "RobotState"]
