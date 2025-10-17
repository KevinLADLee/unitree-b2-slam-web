"""
SLAM 消息类型定义

将 Unitree SDK IDL 消息格式转换为 Python 类型
基于 unitree_sdk2_python 的 IDL 定义
"""

from typing import List, Optional
from dataclasses import dataclass, field
from enum import IntEnum


# ============ 命令类型枚举 ============

class CommandType(IntEnum):
    """QtCommand 命令类型"""

    DELETE = 1              # 删除点/边
    QUERY = 2               # 查询点/边
    START_MAPPING = 3       # 开始建图
    END_MAPPING = 4         # 结束建图
    START_RELOCATION = 6    # 开启重定位
    INIT_POSE = 7           # 重定位初始化位姿
    START_NAVIGATION = 8    # 开启导航
    SINGLE_POINT_NAV = 9    # 单点导航
    LOOP_NAV_DEFAULT = 10   # 多点循环导航（默认）
    LOOP_NAV_CUSTOM = 11    # 多点循环导航（自定义）
    PAUSE_NAV = 13          # 暂停导航
    RESUME_NAV = 14         # 恢复导航
    RETURN_HOME = 15        # 返回起点
    CLOSE_ALL = 99          # 关闭所有节点


class DeleteAttribute(IntEnum):
    """删除命令的 attribute 类型"""

    UNDEFINED = 0    # 未指定
    NODE = 1         # 删除节点
    EDGE = 2         # 删除边


class SystemState(IntEnum):
    """系统状态"""

    ERROR = -1          # 错误
    IDLE = 0            # 空闲
    MAPPING = 2         # 建图中
    NAVIGATION = 3      # 导航中
    RELOCATION = 4      # 重定位开启
    INIT_POSE = 5       # 初始化定位完成
    NAV_NODE_OPEN = 6   # 导航节点打开


class CommandFeedback(IntEnum):
    """命令执行反馈"""

    FAILED = 0      # 执行失败
    SUCCESS = 1     # 执行成功
    WAITING = 2     # 执行等待中
    ERROR = -1      # 执行错误


# ============ 基础消息类型 ============

@dataclass
class String_:
    """ROS2 String 消息"""
    data: str = ""


@dataclass
class Pose:
    """位姿（位置 + 方向）"""
    position: "Point" = field(default_factory=lambda: Point())
    orientation: "Quaternion" = field(default_factory=lambda: Quaternion())


@dataclass
class Point:
    """3D 点"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Quaternion:
    """四元数"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


@dataclass
class PoseWithCovariance:
    """带协方差的位姿"""
    pose: Pose = field(default_factory=Pose)
    covariance: List[float] = field(default_factory=lambda: [0.0] * 36)


@dataclass
class TwistWithCovariance:
    """带协方差的速度"""
    # 简化实现，暂不需要详细字段
    pass


# ============ Odometry 消息 ============

@dataclass
class Odometry_:
    """里程计消息（ROS2 nav_msgs/Odometry）"""

    pose: PoseWithCovariance = field(default_factory=PoseWithCovariance)
    twist: TwistWithCovariance = field(default_factory=TwistWithCovariance)

    # 简化版本，实际还有 header 等字段
    # header: Header = field(default_factory=Header)
    # child_frame_id: str = ""


# ============ Node 消息 ============

@dataclass
class Node_:
    """拓扑节点（graph_msg/Node）"""

    node_name_: List[int] = field(default_factory=list)            # 节点唯一名称
    node_position_x_: List[float] = field(default_factory=list)    # 节点 X 坐标
    node_position_y_: List[float] = field(default_factory=list)    # 节点 Y 坐标
    node_position_z_: List[float] = field(default_factory=list)    # 节点 Z 坐标
    node_yaw_: List[float] = field(default_factory=list)           # 节点 Yaw 值
    node_attribute_: List[int] = field(default_factory=list)       # 节点属性（暂未开放）
    undefined_: List[int] = field(default_factory=list)            # 未定义（暂未开放）
    node_state_2_: List[int] = field(default_factory=list)         # 节点状态 2（暂未开放）
    node_state_3_: List[int] = field(default_factory=list)         # 节点状态 3（暂未开放）
    # node_state_list_: List[Float32MultiArray_] = field(default_factory=list)


# ============ Edge 消息 ============

@dataclass
class Edge_:
    """拓扑边（graph_msg/Edge）"""

    edge_name_: List[int] = field(default_factory=list)           # 边唯一名称
    start_node_name_: List[int] = field(default_factory=list)     # 起始节点名称
    end_node_name_: List[int] = field(default_factory=list)       # 结束节点名称
    edge_length_: List[float] = field(default_factory=list)       # 边长度
    dog_stats_: List[int] = field(default_factory=list)           # 狗状态（暂未开放）
    dog_back_stats_: List[int] = field(default_factory=list)      # 狗返回状态（暂未开放）
    dog_speed_: List[float] = field(default_factory=list)         # 狗速度 (0-1)
    edge_state_: List[int] = field(default_factory=list)          # 边状态（暂未开放）
    edge_state_1_: List[float] = field(default_factory=list)      # 边状态 1（暂未开放）
    edge_state_2_: List[int] = field(default_factory=list)        # 边状态 2（0:停障 1:绕障 3:重规划）
    edge_state_3_: List[int] = field(default_factory=list)        # 边状态 3（暂未开放）
    edge_state_4_: List[int] = field(default_factory=list)        # 边状态 4（暂未开放）
    # edge_state_list_: List[Float32MultiArray_] = field(default_factory=list)


# ============ QtCommand 消息 ============

@dataclass
class QtCommand_:
    """Qt 命令消息（unitree_interfaces/QtCommand）"""

    command_: int = 0                                # 命令类型
    seq_: String_ = field(default_factory=String_)  # 指令唯一识别码 "index:XXX;"
    attribute_: int = 0                              # 属性选择

    floor_index_: List[int] = field(default_factory=list)      # 楼层索引号
    pcdmap_index_: List[int] = field(default_factory=list)     # PCD 地图索引号
    topomap_index_: List[int] = field(default_factory=list)    # 拓扑地图索引号
    node_edge_name_: List[int] = field(default_factory=list)   # 点或边的名称

    # 四元数（旋转）
    quaternion_x_: float = 0.0
    quaternion_y_: float = 0.0
    quaternion_z_: float = 0.0
    quaternion_w_: float = 1.0

    # 欧拉角（暂未使用）
    euler_roll_: float = 0.0
    euler_pitch_: float = 0.0
    euler_yaw_: float = 0.0

    # 平移量
    translation_x_: float = 0.0
    translation_y_: float = 0.0
    translation_z_: float = 0.0

    # 状态（暂未开放）
    state_1_: List[int] = field(default_factory=list)
    state_2_: List[float] = field(default_factory=list)


# ============ QtNode 消息 ============

@dataclass
class QtNode_:
    """Qt 节点消息（unitree_interfaces/QtNode）"""

    seq_: String_ = field(default_factory=String_)  # 指令唯一识别码
    node_: Node_ = field(default_factory=Node_)     # 节点信息


# ============ QtEdge 消息 ============

@dataclass
class QtEdge_:
    """Qt 边消息（unitree_interfaces/QtEdge）"""

    seq_: String_ = field(default_factory=String_)  # 指令唯一识别码
    edge_: Edge_ = field(default_factory=Edge_)     # 边信息


# ============ 辅助数据类 ============

@dataclass
class NodeAttribute:
    """节点属性（便于内部使用）"""
    node_name: int
    node_x: float
    node_y: float
    node_z: float
    node_yaw: float


@dataclass
class EdgeAttribute:
    """边属性（便于内部使用）"""
    edge_name: int
    edge_start: int
    edge_end: int


# ============ Qt Notice 解析 ============

@dataclass
class QtNotice:
    """Qt Notice 消息解析结果"""

    index: int                              # 指令索引
    notice: str                             # 通知消息
    feedback: Optional[int] = None          # 执行反馈 (0:失败 1:成功 2:等待 -1:错误)
    state: Optional[int] = None             # 系统状态
    arrive: Optional[int] = None            # 到达节点（导航反馈）
    finish: Optional[int] = None            # 已完成点数（导航反馈）
    all: Optional[int] = None               # 总点数（导航反馈）
    loop: Optional[int] = None              # 循环次数（导航反馈）
    obstruct: Optional[int] = None          # 是否遇到障碍 (1:否 -1:是)

    @classmethod
    def parse(cls, data: str) -> "QtNotice":
        """
        解析 qt_notice 字符串

        格式: "index:123;feedback:1;state:2;notice:XXX;"
        或: "index:10001;arrive:3;finish:2;all:5;loop:1;obstruct:1;notice:XXX;"

        Args:
            data: qt_notice 数据字符串

        Returns:
            解析后的 QtNotice 对象
        """
        result = {}

        # 解析所有字段
        for pair in data.split(";"):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue

            key, value = pair.split(":", 1)
            key = key.strip()
            value = value.strip()

            # 数值字段转换
            if key in ["index", "feedback", "state", "arrive", "finish", "all", "loop", "obstruct"]:
                try:
                    result[key] = int(value)
                except ValueError:
                    result[key] = None
            else:
                result[key] = value

        return cls(
            index=result.get("index", 0),
            notice=result.get("notice", ""),
            feedback=result.get("feedback"),
            state=result.get("state"),
            arrive=result.get("arrive"),
            finish=result.get("finish"),
            all=result.get("all"),
            loop=result.get("loop"),
            obstruct=result.get("obstruct"),
        )


# ============ 常量定义 ============

# 特殊值
DELETE_ALL = 999  # 删除所有节点/边的特殊值

# 默认值
DEFAULT_FLOOR_INDEX = 0     # 默认楼层索引
DEFAULT_PCDMAP_INDEX = 0    # 默认 PCD 地图索引（将被 MapManager 管理的索引替换）

# 导航反馈索引
NAV_FEEDBACK_INDEX = 10001  # 导航过程反馈的特殊索引


__all__ = [
    # 枚举
    "CommandType",
    "DeleteAttribute",
    "SystemState",
    "CommandFeedback",
    # 基础类型
    "String_",
    "Point",
    "Quaternion",
    "Pose",
    "PoseWithCovariance",
    "Odometry_",
    # 拓扑图类型
    "Node_",
    "Edge_",
    "QtNode_",
    "QtEdge_",
    # 命令类型
    "QtCommand_",
    # 辅助类型
    "NodeAttribute",
    "EdgeAttribute",
    "QtNotice",
    # 常量
    "DELETE_ALL",
    "DEFAULT_FLOOR_INDEX",
    "DEFAULT_PCDMAP_INDEX",
    "NAV_FEEDBACK_INDEX",
]
