"""
API 请求和响应模型

使用 Pydantic 定义所有 API 的数据模型
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


# ============ 通用响应模型 ============

class BaseResponse(BaseModel):
    """基础响应模型"""

    status: str = Field(default="ok", description="响应状态")
    message: str = Field(default="", description="响应消息")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    path: str = Field(..., description="请求路径")
    details: Optional[List[dict]] = Field(None, description="详细错误信息")


# ============ 建图相关模型 ============

class StartMappingRequest(BaseModel):
    """开始建图请求"""

    map_name: str = Field(
        ...,
        description="地图名称，只能包含字母、数字、下划线和连字符",
        min_length=1,
        max_length=50,
        examples=["warehouse_floor1"],
    )
    description: Optional[str] = Field(
        None, description="地图描述", max_length=200, examples=["仓库一楼地图"]
    )

    @field_validator("map_name")
    @classmethod
    def validate_map_name(cls, v: str) -> str:
        """验证地图名称格式"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("地图名称只能包含字母、数字、下划线和连字符")
        return v


class StartMappingResponse(BaseResponse):
    """开始建图响应"""

    map_name: str = Field(..., description="地图名称")
    pcdmap_index: int = Field(..., description="分配的地图索引")


class EndMappingRequest(BaseModel):
    """结束建图请求"""

    map_name: str = Field(..., description="地图名称")
    save_map: bool = Field(default=True, description="是否保存地图")


class EndMappingResponse(BaseResponse):
    """结束建图响应"""

    map_name: str = Field(..., description="地图名称")
    pcdmap_index: int = Field(..., description="地图索引")
    saved: bool = Field(..., description="是否已保存")


class MapInfo(BaseModel):
    """地图信息"""

    name: str = Field(..., description="地图名称")
    index: int = Field(..., description="地图索引")
    description: Optional[str] = Field(None, description="地图描述")
    status: str = Field(..., description="地图状态 (creating/completed/failed/discarded)")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class MapListResponse(BaseModel):
    """地图列表响应"""

    maps: List[MapInfo] = Field(default_factory=list, description="地图列表")
    total: int = Field(..., description="地图总数")


# ============ 重定位相关模型 ============

class StartRelocationRequest(BaseModel):
    """开启重定位请求"""

    map_name: str = Field(..., description="地图名称")


class InitPoseRequest(BaseModel):
    """初始化位姿请求"""

    x: float = Field(default=0.0, description="X 坐标 (米)")
    y: float = Field(default=0.0, description="Y 坐标 (米)")
    z: float = Field(default=0.0, description="Z 坐标 (米)")
    qx: Optional[float] = Field(default=None, description="四元数 X")
    qy: Optional[float] = Field(default=None, description="四元数 Y")
    qz: Optional[float] = Field(default=None, description="四元数 Z")
    qw: Optional[float] = Field(default=None, description="四元数 W")
    roll: Optional[float] = Field(default=None, description="Roll 角度（弧度）")
    pitch: Optional[float] = Field(default=None, description="Pitch 角度（弧度）")
    yaw: Optional[float] = Field(default=None, description="Yaw 角度（弧度）")


# ============ 导航相关模型 ============

class StartNavigationRequest(BaseModel):
    """开启导航请求"""

    map_name: str = Field(..., description="地图名称")


class SinglePointNavRequest(BaseModel):
    """单点导航请求"""

    target_node: int = Field(..., description="目标节点 ID", ge=1, examples=[5])


class LoopNavRequest(BaseModel):
    """多点循环导航请求"""

    node_sequence: Optional[List[int]] = Field(
        None,
        description="节点序列，None 表示默认循环所有节点",
        examples=[[1, 2, 3, 4]],
    )


class PauseNavigationRequest(BaseModel):
    """暂停导航请求"""

    pass


class ResumeNavigationRequest(BaseModel):
    """恢复导航请求"""

    pass


class ReturnHomeRequest(BaseModel):
    """返回起点请求"""

    pass


# ============ 拓扑图相关模型 ============

class AddNodeRequest(BaseModel):
    """添加节点请求（基于当前位姿）"""

    node_name: Optional[str] = Field(None, description="节点名称（可选）")


class AddNodeResponse(BaseResponse):
    """添加节点响应"""

    node_id: int = Field(..., description="节点 ID")
    x: float = Field(..., description="X 坐标")
    y: float = Field(..., description="Y 坐标")
    z: float = Field(..., description="Z 坐标")
    yaw: float = Field(..., description="Yaw 角度")


class AddEdgeRequest(BaseModel):
    """添加边请求"""

    start_node: int = Field(..., description="起始节点 ID", ge=1)
    end_node: int = Field(..., description="结束节点 ID", ge=1)
    speed: float = Field(default=1.0, description="速度 (0-1)", ge=0.0, le=1.0)


class SaveTopologyRequest(BaseModel):
    """保存拓扑图请求"""

    pass


class DeleteNodesRequest(BaseModel):
    """删除节点请求"""

    node_ids: List[int] = Field(
        default=[999], description="要删除的节点 ID 列表，[999] 表示删除全部"
    )


class DeleteEdgesRequest(BaseModel):
    """删除边请求"""

    edge_ids: List[int] = Field(
        default=[999], description="要删除的边 ID 列表，[999] 表示删除全部"
    )


class NodeInfo(BaseModel):
    """节点信息"""

    node_id: int = Field(..., description="节点 ID")
    x: float = Field(..., description="X 坐标")
    y: float = Field(..., description="Y 坐标")
    z: float = Field(..., description="Z 坐标")
    yaw: float = Field(..., description="Yaw 角度")
    name: Optional[str] = Field(None, description="节点名称")


class EdgeInfo(BaseModel):
    """边信息"""

    edge_id: int = Field(..., description="边 ID")
    start_node: int = Field(..., description="起始节点")
    end_node: int = Field(..., description="结束节点")
    length: float = Field(..., description="边长度")
    speed: float = Field(..., description="速度 (0-1)")


class TopologyResponse(BaseModel):
    """拓扑图响应"""

    nodes: List[NodeInfo] = Field(default_factory=list, description="节点列表")
    edges: List[EdgeInfo] = Field(default_factory=list, description="边列表")


# ============ 状态查询相关模型 ============

class SystemStatus(BaseModel):
    """系统状态"""

    state: str = Field(
        ...,
        description="系统状态 (idle/mapping/navigation/relocation/error)",
    )
    mode: str = Field(..., description="运行模式 (simulator/real)")
    timestamp: float = Field(..., description="时间戳")


class OdometryData(BaseModel):
    """里程计数据"""

    x: float = Field(..., description="X 坐标")
    y: float = Field(..., description="Y 坐标")
    z: float = Field(..., description="Z 坐标")
    qx: float = Field(..., description="四元数 X")
    qy: float = Field(..., description="四元数 Y")
    qz: float = Field(..., description="四元数 Z")
    qw: float = Field(..., description="四元数 W")
    timestamp: float = Field(..., description="时间戳")


# ============ 通用 API 响应模型 ============

class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


# ============ 扩展响应模型 ============

class StartRelocationResponse(ApiResponse):
    """开启重定位响应"""
    pass


class InitPoseResponse(ApiResponse):
    """初始化位姿响应"""
    pass


class StartNavigationResponse(ApiResponse):
    """开启导航响应"""
    pass


class SinglePointNavResponse(ApiResponse):
    """单点导航响应"""
    pass


class LoopNavigationResponse(ApiResponse):
    """循环导航响应"""
    pass


class PauseNavigationResponse(ApiResponse):
    """暂停导航响应"""
    pass


class ResumeNavigationResponse(ApiResponse):
    """恢复导航响应"""
    pass


class ReturnHomeResponse(ApiResponse):
    """返回起点响应"""
    pass


class SaveTopologyResponse(ApiResponse):
    """保存拓扑图响应"""
    pass


class ClearTopologyResponse(ApiResponse):
    """清除拓扑图响应"""
    pass


class GetTopologyResponse(ApiResponse):
    """获取拓扑图响应"""
    pass


class DeleteNodesResponse(ApiResponse):
    """删除节点响应"""
    pass


class DeleteEdgesResponse(ApiResponse):
    """删除边响应"""
    pass


class GetSystemStatusResponse(ApiResponse):
    """获取系统状态响应"""
    pass


class GetOdometryResponse(ApiResponse):
    """获取里程计响应"""
    pass


class GetCommandStatsResponse(ApiResponse):
    """获取命令统计响应"""
    pass


# ============ WebSocket 消息模型 ============

class WebSocketMessage(BaseModel):
    """WebSocket 消息基础模型"""

    type: str = Field(..., description="消息类型")
    data: dict = Field(..., description="消息数据")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="时间戳"
    )


__all__ = [
    # 通用
    "BaseResponse",
    "ErrorResponse",
    "ApiResponse",
    # 建图
    "StartMappingRequest",
    "StartMappingResponse",
    "EndMappingRequest",
    "EndMappingResponse",
    "MapInfo",
    "MapListResponse",
    # 重定位
    "StartRelocationRequest",
    "StartRelocationResponse",
    "InitPoseRequest",
    "InitPoseResponse",
    # 导航
    "StartNavigationRequest",
    "StartNavigationResponse",
    "SinglePointNavRequest",
    "SinglePointNavResponse",
    "LoopNavRequest",
    "LoopNavigationResponse",
    "PauseNavigationRequest",
    "PauseNavigationResponse",
    "ResumeNavigationRequest",
    "ResumeNavigationResponse",
    "ReturnHomeRequest",
    "ReturnHomeResponse",
    # 拓扑图
    "AddNodeRequest",
    "AddNodeResponse",
    "AddEdgeRequest",
    "SaveTopologyRequest",
    "SaveTopologyResponse",
    "ClearTopologyResponse",
    "GetTopologyResponse",
    "DeleteNodesRequest",
    "DeleteNodesResponse",
    "DeleteEdgesRequest",
    "DeleteEdgesResponse",
    "NodeInfo",
    "EdgeInfo",
    "TopologyResponse",
    # 状态
    "SystemStatus",
    "OdometryData",
    "GetSystemStatusResponse",
    "GetOdometryResponse",
    "GetCommandStatsResponse",
    # WebSocket
    "WebSocketMessage",
]
