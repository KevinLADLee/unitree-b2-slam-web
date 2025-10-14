"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import IntEnum


class SystemState(IntEnum):
    """系统状态枚举"""
    IDLE = 0
    ERROR = -1
    MAPPING = 2
    NAVIGATION = 3
    RELOCATION_OPEN = 4
    LOCALIZATION_COMPLETE = 5
    NAVIGATION_NODE_OPEN = 6


class FeedbackStatus(IntEnum):
    """反馈状态"""
    FAILURE = 0
    SUCCESS = 1
    WAITING = 2


class Node(BaseModel):
    """拓扑节点"""
    name: str
    x: float
    y: float
    z: float = 0.0
    yaw: float = 0.0


class Edge(BaseModel):
    """拓扑边"""
    name: str
    start_node: str
    end_node: str
    length: float
    speed: float = Field(default=0.5, ge=0.0, le=1.0)
    avoid_method: int = Field(default=0, description="0=stop, 1=avoid, 3=replan")


class Feedback(BaseModel):
    """标准反馈"""
    index: str
    feedback: int  # 0=failure, 1=success, 2=waiting
    state: int
    notice: str


class PoseInput(BaseModel):
    """位姿输入"""
    x: float
    y: float
    yaw: float


class NavigationTarget(BaseModel):
    """导航目标"""
    node_name: str


class NavigationTargets(BaseModel):
    """多节点导航"""
    node_names: List[str]
    mode: str = "loop"  # "loop" or "once"


class WaypointsFile(BaseModel):
    """路点文件格式"""
    waypoints: List[Node]
    mode: str = "loop"
    metadata: Optional[dict] = None


class NavigationTask(BaseModel):
    """导航任务"""
    id: str
    name: str
    node_names: List[str]
    mode: str = "loop"  # "loop" or "once"
    created_at: str
    updated_at: Optional[str] = None


class CurrentPosition(BaseModel):
    """当前实时位置"""
    x: float
    y: float
    z: float
    yaw: float
    timestamp: str


class TopologyMap(BaseModel):
    """拓扑地图 (用于保存/加载)"""
    nodes: List[Node]
    edges: List[Edge]
    metadata: Optional[dict] = None


class MappingConfig(BaseModel):
    """建图配置"""
    pcdmap_index: List[int] = Field(default_factory=list, description="点云地图索引列表 (sequence<unsigned short>)")


class RelocalizationConfig(BaseModel):
    """重定位配置"""
    pcdmap_index: List[int] = Field(default_factory=list, description="点云地图索引列表 (sequence<unsigned short>)")
    x: Optional[float] = None
    y: Optional[float] = None
    yaw: Optional[float] = None


class VisualizationConfig(BaseModel):
    """2D 地图可视化配置"""
    map_topic: str = Field(default="/map", description="OccupancyGrid 地图 topic")
    scan_topic: str = Field(default="/scan", description="LaserScan 激光扫描 topic")
    odom_topic: str = Field(default="/odom", description="Odometry 里程计 topic")
    use_sim_time: bool = Field(default=False, description="是否使用仿真时间")

