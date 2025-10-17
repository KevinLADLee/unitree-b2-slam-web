"""
命令构建器

提供简洁的 API 来构建各种 SLAM 命令
"""

from typing import List, Optional, Tuple
import math
from slam.message_types import (
    QtCommand_,
    QtNode_,
    QtEdge_,
    Node_,
    Edge_,
    String_,
    CommandType,
    DeleteAttribute,
    NodeAttribute,
    EdgeAttribute,
    DEFAULT_FLOOR_INDEX,
    DELETE_ALL,
)
from logger import get_logger

logger = get_logger("command_builder")


class CommandBuilder:
    """SLAM 命令构建器"""

    def __init__(self, index_generator):
        """
        初始化命令构建器

        Args:
            index_generator: 索引生成器（返回递增的命令索引）
        """
        self.index_generator = index_generator

    def _get_next_index(self) -> int:
        """获取下一个命令索引"""
        return self.index_generator()

    def _create_seq(self, index: Optional[int] = None) -> String_:
        """
        创建序列号字符串

        Args:
            index: 命令索引，如果为 None 则自动生成

        Returns:
            String_ 对象
        """
        if index is None:
            index = self._get_next_index()
        return String_(data=f"index:{index};")

    # ============ 建图命令 ============

    def build_start_mapping(self) -> Tuple[int, QtCommand_]:
        """
        构建开始建图命令

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.START_MAPPING
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 START_MAPPING 命令, index={index}")
        return index, cmd

    def build_end_mapping(
        self, pcdmap_index: int, floor_index: int = DEFAULT_FLOOR_INDEX, save: bool = True
    ) -> Tuple[int, QtCommand_]:
        """
        构建结束建图命令

        Args:
            pcdmap_index: PCD 地图索引
            floor_index: 楼层索引（默认 0）
            save: 是否保存地图

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.END_MAPPING
        cmd.seq_ = self._create_seq(index)
        cmd.attribute_ = 0 if save else 1
        cmd.floor_index_ = [floor_index]
        cmd.pcdmap_index_ = [pcdmap_index]

        logger.debug(
            f"构建 END_MAPPING 命令, index={index}, "
            f"pcdmap_index={pcdmap_index}, save={save}"
        )
        return index, cmd

    # ============ 重定位命令 ============

    def build_start_relocation(self) -> Tuple[int, QtCommand_]:
        """
        构建开启重定位命令

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.START_RELOCATION
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 START_RELOCATION 命令, index={index}")
        return index, cmd

    def build_init_pose(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        qx: float = 0.0,
        qy: float = 0.0,
        qz: float = 0.0,
        qw: float = 1.0,
    ) -> Tuple[int, QtCommand_]:
        """
        构建初始化位姿命令

        Args:
            x, y, z: 位置坐标
            qx, qy, qz, qw: 四元数

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.INIT_POSE
        cmd.seq_ = self._create_seq(index)
        cmd.translation_x_ = x
        cmd.translation_y_ = y
        cmd.translation_z_ = z
        cmd.quaternion_x_ = qx
        cmd.quaternion_y_ = qy
        cmd.quaternion_z_ = qz
        cmd.quaternion_w_ = qw

        logger.debug(
            f"构建 INIT_POSE 命令, index={index}, "
            f"pos=({x:.2f}, {y:.2f}, {z:.2f}), "
            f"quat=({qx:.2f}, {qy:.2f}, {qz:.2f}, {qw:.2f})"
        )
        return index, cmd

    # ============ 导航命令 ============

    def build_start_navigation(self) -> Tuple[int, QtCommand_]:
        """
        构建开启导航命令

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.START_NAVIGATION
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 START_NAVIGATION 命令, index={index}")
        return index, cmd

    def build_single_point_nav(self, target_node: int) -> Tuple[int, QtCommand_]:
        """
        构建单点导航命令

        Args:
            target_node: 目标节点 ID

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.SINGLE_POINT_NAV
        cmd.seq_ = self._create_seq(index)
        cmd.node_edge_name_ = [target_node]

        logger.debug(f"构建 SINGLE_POINT_NAV 命令, index={index}, target={target_node}")
        return index, cmd

    def build_loop_navigation(
        self, node_sequence: Optional[List[int]] = None
    ) -> Tuple[int, QtCommand_]:
        """
        构建多点循环导航命令

        Args:
            node_sequence: 节点序列，None 表示默认循环

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()

        if node_sequence is None:
            # 默认循环
            cmd.command_ = CommandType.LOOP_NAV_DEFAULT
            logger.debug(f"构建 LOOP_NAV_DEFAULT 命令, index={index}")
        else:
            # 自定义循环
            cmd.command_ = CommandType.LOOP_NAV_CUSTOM
            cmd.node_edge_name_ = list(node_sequence)
            logger.debug(
                f"构建 LOOP_NAV_CUSTOM 命令, index={index}, "
                f"sequence={node_sequence}"
            )

        cmd.seq_ = self._create_seq(index)
        return index, cmd

    def build_pause_navigation(self) -> Tuple[int, QtCommand_]:
        """构建暂停导航命令"""
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.PAUSE_NAV
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 PAUSE_NAV 命令, index={index}")
        return index, cmd

    def build_resume_navigation(self) -> Tuple[int, QtCommand_]:
        """构建恢复导航命令"""
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.RESUME_NAV
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 RESUME_NAV 命令, index={index}")
        return index, cmd

    def build_return_home(self) -> Tuple[int, QtCommand_]:
        """构建返回起点命令"""
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.RETURN_HOME
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 RETURN_HOME 命令, index={index}")
        return index, cmd

    # ============ 拓扑图命令 ============

    def build_delete_nodes(self, node_ids: List[int] = None) -> Tuple[int, QtCommand_]:
        """
        构建删除节点命令

        Args:
            node_ids: 要删除的节点 ID 列表，None 或 [999] 表示删除全部

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.DELETE
        cmd.seq_ = self._create_seq(index)
        cmd.attribute_ = DeleteAttribute.NODE

        if node_ids is None or node_ids == [DELETE_ALL]:
            cmd.node_edge_name_ = [DELETE_ALL]
            logger.debug(f"构建 DELETE 命令 (所有节点), index={index}")
        else:
            cmd.node_edge_name_ = list(node_ids)
            logger.debug(f"构建 DELETE 命令 (节点), index={index}, nodes={node_ids}")

        return index, cmd

    def build_delete_edges(self, edge_ids: List[int] = None) -> Tuple[int, QtCommand_]:
        """
        构建删除边命令

        Args:
            edge_ids: 要删除的边 ID 列表，None 或 [999] 表示删除全部

        Returns:
            (命令索引, QtCommand 对象)
        """
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.DELETE
        cmd.seq_ = self._create_seq(index)
        cmd.attribute_ = DeleteAttribute.EDGE

        if edge_ids is None or edge_ids == [DELETE_ALL]:
            cmd.node_edge_name_ = [DELETE_ALL]
            logger.debug(f"构建 DELETE 命令 (所有边), index={index}")
        else:
            cmd.node_edge_name_ = list(edge_ids)
            logger.debug(f"构建 DELETE 命令 (边), index={index}, edges={edge_ids}")

        return index, cmd

    def build_save_nodes(self, nodes: List[NodeAttribute]) -> Tuple[int, QtNode_]:
        """
        构建保存节点命令

        Args:
            nodes: 节点列表

        Returns:
            (命令索引, QtNode 对象)
        """
        index = self._get_next_index()
        qt_node = QtNode_()
        qt_node.seq_ = self._create_seq(index)

        node_msg = Node_()
        for node in nodes:
            node_msg.node_name_.append(node.node_name)
            node_msg.node_position_x_.append(node.node_x)
            node_msg.node_position_y_.append(node.node_y)
            node_msg.node_position_z_.append(node.node_z)
            node_msg.node_yaw_.append(node.node_yaw)
            node_msg.node_attribute_.append(0)  # 暂未开放
            node_msg.undefined_.append(0)
            node_msg.node_state_2_.append(0)
            node_msg.node_state_3_.append(0)

        qt_node.node_ = node_msg

        logger.debug(f"构建 SAVE_NODES 命令, index={index}, count={len(nodes)}")
        return index, qt_node

    def build_save_edges(self, edges: List[EdgeAttribute]) -> Tuple[int, QtEdge_]:
        """
        构建保存边命令

        Args:
            edges: 边列表

        Returns:
            (命令索引, QtEdge 对象)
        """
        index = self._get_next_index()
        qt_edge = QtEdge_()
        qt_edge.seq_ = self._create_seq(index)

        edge_msg = Edge_()
        for edge in edges:
            edge_msg.edge_name_.append(edge.edge_name)
            edge_msg.start_node_name_.append(edge.edge_start)
            edge_msg.end_node_name_.append(edge.edge_end)
            edge_msg.edge_length_.append(0.0)
            edge_msg.dog_speed_.append(1.0)         # 速度 0-1
            edge_msg.edge_state_2_.append(0)        # 0:停障 1:绕障 3:重规划
            # 暂未开放的字段
            edge_msg.dog_stats_.append(0)
            edge_msg.dog_back_stats_.append(0)
            edge_msg.edge_state_.append(0)
            edge_msg.edge_state_1_.append(0.0)
            edge_msg.edge_state_3_.append(0)
            edge_msg.edge_state_4_.append(0)

        qt_edge.edge_ = edge_msg

        logger.debug(f"构建 SAVE_EDGES 命令, index={index}, count={len(edges)}")
        return index, qt_edge

    # ============ 系统命令 ============

    def build_close_all(self) -> Tuple[int, QtCommand_]:
        """构建关闭所有节点命令"""
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.command_ = CommandType.CLOSE_ALL
        cmd.seq_ = self._create_seq(index)

        logger.debug(f"构建 CLOSE_ALL 命令, index={index}")
        return index, cmd


# ============ 辅助函数 ============

def quaternion_from_euler(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """
    从欧拉角转换为四元数

    Args:
        roll: X 轴旋转
        pitch: Y 轴旋转
        yaw: Z 轴旋转

    Returns:
        (qx, qy, qz, qw)
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy

    return qx, qy, qz, qw


def yaw_from_quaternion(qx: float, qy: float, qz: float, qw: float) -> float:
    """
    从四元数提取 yaw 角

    Args:
        qx, qy, qz, qw: 四元数

    Returns:
        yaw 角（弧度）
    """
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


__all__ = [
    "CommandBuilder",
    "quaternion_from_euler",
    "yaw_from_quaternion",
]
