"""
ROS消息模拟器 - 为前端可视化提供测试数据
模拟ROS2标准消息格式：nav_msgs/OccupancyGrid, sensor_msgs/LaserScan, nav_msgs/Odometry
"""
from dataclasses import dataclass, field
from typing import List, Tuple
import math
import random
from datetime import datetime


@dataclass
class OccupancyGridData:
    """模拟 nav_msgs/OccupancyGrid"""
    width: int = 200        # 地图宽度（像素）
    height: int = 200       # 地图高度（像素）
    resolution: float = 0.05  # 分辨率（米/像素）
    origin_x: float = -5.0   # 地图原点X
    origin_y: float = -5.0   # 地图原点Y
    data: List[int] = field(default_factory=list)

    def __post_init__(self):
        if not self.data:
            self.data = self._generate_test_map()

    def _generate_test_map(self) -> List[int]:
        """生成测试地图：中间自由空间，周围障碍物，随机障碍物"""
        data = []
        center_x = self.width // 2
        center_y = self.height // 2

        for y in range(self.height):
            for x in range(self.width):
                # 外边界是障碍物
                if x < 10 or x > self.width - 10 or y < 10 or y > self.height - 10:
                    data.append(100)
                # 添加一些矩形障碍物（模拟房间墙壁）
                elif (30 < x < 50 and 30 < y < 100) or (150 < x < 170 and 100 < y < 170):
                    data.append(100)
                # 添加小的随机障碍物
                elif random.random() < 0.02:
                    data.append(100)
                # 其他是自由空间
                else:
                    data.append(0)

        return data


@dataclass
class LaserScanData:
    """模拟 sensor_msgs/LaserScan"""
    angle_min: float = -3.14159  # -180度
    angle_max: float = 3.14159   # +180度
    angle_increment: float = 0.0174533  # ~1度
    range_min: float = 0.1
    range_max: float = 10.0
    ranges: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.ranges:
            self.ranges = self._generate_scan()

    def _generate_scan(self) -> List[float]:
        """生成360个激光点（360度扫描）"""
        num_points = int((self.angle_max - self.angle_min) / self.angle_increment)
        ranges = []

        for i in range(num_points):
            angle = self.angle_min + i * self.angle_increment
            # 模拟不同方向有不同距离的障碍物
            if -0.5 < angle < 0.5:  # 前方较远
                distance = random.uniform(3.0, 8.0)
            elif abs(angle) > 2.5:  # 后方较近
                distance = random.uniform(0.5, 2.0)
            else:  # 侧方中等距离
                distance = random.uniform(1.5, 5.0)

            ranges.append(distance)

        return ranges


@dataclass
class OdometryData:
    """模拟 nav_msgs/Odometry"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ROSMessageSimulator:
    """ROS消息模拟器"""

    def __init__(self):
        self.occupancy_grid = OccupancyGridData()
        self.laser_scan = LaserScanData()
        self.odometry = OdometryData()
        self.is_moving = False
        self.trajectory: List[Tuple[float, float]] = []
        self.seq_counter = 0

    def update_robot_pose(self, x: float, y: float, yaw: float):
        """更新机器人位姿"""
        self.odometry.x = x
        self.odometry.y = y
        self.odometry.yaw = yaw
        self.odometry.timestamp = datetime.now().isoformat()

        # 记录轨迹
        self.trajectory.append((x, y))
        if len(self.trajectory) > 100:  # 只保留最近100个点
            self.trajectory.pop(0)

    def simulate_motion(self, linear: float, angular: float, dt: float = 0.1):
        """模拟机器人运动（简单的差分驱动模型）"""
        # 更新速度
        self.odometry.linear_velocity = linear
        self.odometry.angular_velocity = angular

        # 计算新位置
        dx = linear * math.cos(self.odometry.yaw) * dt
        dy = linear * math.sin(self.odometry.yaw) * dt
        dyaw = angular * dt

        self.update_robot_pose(
            self.odometry.x + dx,
            self.odometry.y + dy,
            self.odometry.yaw + dyaw
        )

        # 更新激光扫描数据（模拟扫描更新）
        self.laser_scan = LaserScanData()

    def get_map_message(self) -> dict:
        """获取OccupancyGrid消息（ROS2标准格式）"""
        self.seq_counter += 1
        return {
            "header": {
                "seq": self.seq_counter,
                "stamp": datetime.now().timestamp(),
                "frame_id": "map"
            },
            "info": {
                "map_load_time": datetime.now().timestamp(),
                "resolution": self.occupancy_grid.resolution,
                "width": self.occupancy_grid.width,
                "height": self.occupancy_grid.height,
                "origin": {
                    "position": {
                        "x": self.occupancy_grid.origin_x,
                        "y": self.occupancy_grid.origin_y,
                        "z": 0.0
                    },
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0,
                        "w": 1.0
                    }
                }
            },
            "data": self.occupancy_grid.data
        }

    def get_scan_message(self) -> dict:
        """获取LaserScan消息（ROS2标准格式）"""
        self.seq_counter += 1
        return {
            "header": {
                "seq": self.seq_counter,
                "stamp": datetime.now().timestamp(),
                "frame_id": "laser"
            },
            "angle_min": self.laser_scan.angle_min,
            "angle_max": self.laser_scan.angle_max,
            "angle_increment": self.laser_scan.angle_increment,
            "time_increment": 0.0,
            "scan_time": 0.1,
            "range_min": self.laser_scan.range_min,
            "range_max": self.laser_scan.range_max,
            "ranges": self.laser_scan.ranges,
            "intensities": []
        }

    def get_odom_message(self) -> dict:
        """获取Odometry消息（ROS2标准格式）"""
        self.seq_counter += 1

        # 将yaw转换为四元数
        qz = math.sin(self.odometry.yaw / 2)
        qw = math.cos(self.odometry.yaw / 2)

        return {
            "header": {
                "seq": self.seq_counter,
                "stamp": datetime.now().timestamp(),
                "frame_id": "odom"
            },
            "child_frame_id": "base_link",
            "pose": {
                "pose": {
                    "position": {
                        "x": self.odometry.x,
                        "y": self.odometry.y,
                        "z": self.odometry.z
                    },
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": qz,
                        "w": qw
                    }
                },
                "covariance": [0.0] * 36
            },
            "twist": {
                "twist": {
                    "linear": {
                        "x": self.odometry.linear_velocity,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "angular": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": self.odometry.angular_velocity
                    }
                },
                "covariance": [0.0] * 36
            }
        }

    def clear_trajectory(self):
        """清空轨迹"""
        self.trajectory.clear()

    def reset_pose(self):
        """重置位姿到原点"""
        self.update_robot_pose(0.0, 0.0, 0.0)
        self.odometry.linear_velocity = 0.0
        self.odometry.angular_velocity = 0.0
        self.clear_trajectory()
