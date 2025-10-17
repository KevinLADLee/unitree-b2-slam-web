"""
Qt Notice 响应模拟器

模拟 SLAM 系统对命令的响应
"""

import asyncio
from typing import Optional, Callable, Dict
from enum import IntEnum

from slam.message_types import (
    QtCommand_,
    QtNode_,
    QtEdge_,
    String_,
    CommandType,
    CommandFeedback,
    SystemState,
)
from logger import get_logger

logger = get_logger("notice_simulator")


class SimulationState(IntEnum):
    """仿真状态"""
    IDLE = 0
    MAPPING = 1
    RELOCATION = 2
    NAVIGATION = 3


class NoticeSimulator:
    """Qt Notice 响应模拟器"""

    def __init__(self, response_delay: float = 0.5):
        """
        初始化 Notice 模拟器

        Args:
            response_delay: 响应延迟（秒）
        """
        self.response_delay = response_delay

        # 当前状态
        self.state = SimulationState.IDLE
        self.current_map_index: Optional[int] = None

        # 回调函数
        self._callback: Optional[Callable] = None

        # 拓扑图数据
        self.nodes: Dict[int, tuple] = {}  # node_id -> (x, y, z, yaw)
        self.edges: Dict[int, tuple] = {}  # edge_id -> (start, end)

        logger.info(f"NoticeSimulator 初始化: delay={response_delay}s")

    def set_callback(self, callback: Callable[[String_], None]):
        """
        设置 Notice 回调

        Args:
            callback: 回调函数
        """
        self._callback = callback
        logger.debug("Notice 回调已设置")

    async def handle_command(self, cmd: QtCommand_):
        """
        处理命令

        Args:
            cmd: Qt 命令
        """
        # 解析索引
        index = self._parse_index(cmd.seq_.data)

        logger.info(f"收到命令: type={cmd.command_}, index={index}")

        # 延迟模拟处理时间
        await asyncio.sleep(self.response_delay)

        # 根据命令类型处理
        if cmd.command_ == CommandType.START_MAPPING:
            await self._handle_start_mapping(index)

        elif cmd.command_ == CommandType.END_MAPPING:
            await self._handle_end_mapping(index, cmd)

        elif cmd.command_ == CommandType.START_RELOCATION:
            await self._handle_start_relocation(index)

        elif cmd.command_ == CommandType.INIT_POSE:
            await self._handle_init_pose(index)

        elif cmd.command_ == CommandType.START_NAVIGATION:
            await self._handle_start_navigation(index)

        elif cmd.command_ == CommandType.SINGLE_POINT_NAV:
            await self._handle_single_point_nav(index, cmd)

        elif cmd.command_ == CommandType.LOOP_NAV_DEFAULT:
            await self._handle_loop_navigation(index, None)

        elif cmd.command_ == CommandType.LOOP_NAV_CUSTOM:
            await self._handle_loop_navigation(index, cmd.node_edge_name_)

        elif cmd.command_ == CommandType.PAUSE_NAV:
            await self._handle_pause_navigation(index)

        elif cmd.command_ == CommandType.RESUME_NAV:
            await self._handle_resume_navigation(index)

        elif cmd.command_ == CommandType.RETURN_HOME:
            await self._handle_return_home(index)

        elif cmd.command_ == CommandType.DELETE:
            await self._handle_delete(index, cmd)

        elif cmd.command_ == CommandType.CLOSE_ALL:
            await self._handle_close_all(index)

        else:
            logger.warning(f"未知命令类型: {cmd.command_}")
            await self._send_notice(index, CommandFeedback.FAILED, None, "未知命令")

    async def handle_save_nodes(self, qt_node: QtNode_):
        """
        处理保存节点

        Args:
            qt_node: Qt 节点消息
        """
        index = self._parse_index(qt_node.seq_.data)
        logger.info(f"保存节点: index={index}, count={len(qt_node.node_.node_name_)}")

        # 保存节点数据
        for i, node_id in enumerate(qt_node.node_.node_name_):
            self.nodes[node_id] = (
                qt_node.node_.node_position_x_[i],
                qt_node.node_.node_position_y_[i],
                qt_node.node_.node_position_z_[i],
                qt_node.node_.node_yaw_[i],
            )

        await asyncio.sleep(self.response_delay)
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            None,
            f"已保存 {len(qt_node.node_.node_name_)} 个节点"
        )

    async def handle_save_edges(self, qt_edge: QtEdge_):
        """
        处理保存边

        Args:
            qt_edge: Qt 边消息
        """
        index = self._parse_index(qt_edge.seq_.data)
        logger.info(f"保存边: index={index}, count={len(qt_edge.edge_.edge_name_)}")

        # 保存边数据
        for i, edge_id in enumerate(qt_edge.edge_.edge_name_):
            self.edges[edge_id] = (
                qt_edge.edge_.start_node_name_[i],
                qt_edge.edge_.end_node_name_[i],
            )

        await asyncio.sleep(self.response_delay)
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            None,
            f"已保存 {len(qt_edge.edge_.edge_name_)} 条边"
        )

    # ============ 命令处理方法 ============

    async def _handle_start_mapping(self, index: int):
        """处理开始建图"""
        self.state = SimulationState.MAPPING
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.MAPPING,
            "建图已开始"
        )

    async def _handle_end_mapping(self, index: int, cmd: QtCommand_):
        """处理结束建图"""
        self.current_map_index = cmd.pcdmap_index_[0] if cmd.pcdmap_index_ else 0
        self.state = SimulationState.IDLE

        if cmd.attribute_ == 0:  # 保存地图
            await self._send_notice(
                index,
                CommandFeedback.SUCCESS,
                SystemState.IDLE,
                f"建图已结束，地图 {self.current_map_index} 已保存"
            )
        else:  # 不保存
            await self._send_notice(
                index,
                CommandFeedback.SUCCESS,
                SystemState.IDLE,
                "建图已取消"
            )

    async def _handle_start_relocation(self, index: int):
        """处理开启重定位"""
        self.state = SimulationState.RELOCATION
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.RELOCATION,
            "重定位已开启"
        )

    async def _handle_init_pose(self, index: int):
        """处理初始化位姿"""
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.INIT_POSE,
            "位姿初始化成功"
        )

    async def _handle_start_navigation(self, index: int):
        """处理开启导航"""
        self.state = SimulationState.NAVIGATION
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAV_NODE_OPEN,
            "导航已开启"
        )

    async def _handle_single_point_nav(self, index: int, cmd: QtCommand_):
        """处理单点导航"""
        target = cmd.node_edge_name_[0] if cmd.node_edge_name_ else 0
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAVIGATION,
            f"开始导航到节点 {target}"
        )

        # 模拟导航过程（异步）
        asyncio.create_task(self._simulate_navigation([target]))

    async def _handle_loop_navigation(self, index: int, sequence):
        """处理循环导航"""
        if sequence:
            msg = f"开始循环导航: {sequence}"
        else:
            msg = "开始默认循环导航"

        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAVIGATION,
            msg
        )

        # 模拟导航过程
        if sequence:
            asyncio.create_task(self._simulate_navigation(sequence))

    async def _handle_pause_navigation(self, index: int):
        """处理暂停导航"""
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAVIGATION,
            "导航已暂停"
        )

    async def _handle_resume_navigation(self, index: int):
        """处理恢复导航"""
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAVIGATION,
            "导航已恢复"
        )

    async def _handle_return_home(self, index: int):
        """处理返回起点"""
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.NAVIGATION,
            "开始返回起点"
        )

    async def _handle_delete(self, index: int, cmd: QtCommand_):
        """处理删除"""
        if cmd.attribute_ == 1:  # 删除节点
            if cmd.node_edge_name_ == [999]:
                self.nodes.clear()
                msg = "已删除所有节点"
            else:
                for node_id in cmd.node_edge_name_:
                    self.nodes.pop(node_id, None)
                msg = f"已删除 {len(cmd.node_edge_name_)} 个节点"

        elif cmd.attribute_ == 2:  # 删除边
            if cmd.node_edge_name_ == [999]:
                self.edges.clear()
                msg = "已删除所有边"
            else:
                for edge_id in cmd.node_edge_name_:
                    self.edges.pop(edge_id, None)
                msg = f"已删除 {len(cmd.node_edge_name_)} 条边"
        else:
            msg = "删除操作完成"

        await self._send_notice(index, CommandFeedback.SUCCESS, None, msg)

    async def _handle_close_all(self, index: int):
        """处理关闭所有节点"""
        self.state = SimulationState.IDLE
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            SystemState.IDLE,
            "所有节点已关闭"
        )

    # ============ 辅助方法 ============

    async def _simulate_navigation(self, node_sequence: list):
        """
        模拟导航过程

        Args:
            node_sequence: 节点序列
        """
        for i, node_id in enumerate(node_sequence):
            # 等待模拟导航时间
            await asyncio.sleep(2.0)

            # 发送到达通知
            notice_data = (
                f"index:10001;"
                f"arrive:{node_id};"
                f"finish:{i+1};"
                f"all:{len(node_sequence)};"
                f"loop:1;"
                f"obstruct:1;"
                f"notice:到达节点 {node_id};"
            )

            if self._callback:
                self._callback(String_(data=notice_data))

            logger.info(f"导航: 到达节点 {node_id} ({i+1}/{len(node_sequence)})")

    async def _send_notice(
        self,
        index: int,
        feedback: int,
        state: Optional[int],
        notice: str
    ):
        """
        发送 Notice 消息

        Args:
            index: 命令索引
            feedback: 反馈值
            state: 系统状态
            notice: 通知消息
        """
        notice_data = f"index:{index};feedback:{feedback};"

        if state is not None:
            notice_data += f"state:{state};"

        notice_data += f"notice:{notice};"

        if self._callback:
            self._callback(String_(data=notice_data))

        logger.debug(f"发送 Notice: {notice_data}")

    def _parse_index(self, seq_data: str) -> int:
        """
        从序列字符串中解析索引

        Args:
            seq_data: 序列字符串 "index:123;"

        Returns:
            索引值
        """
        try:
            start = seq_data.find("index:") + 6
            end = seq_data.find(";", start)
            return int(seq_data[start:end])
        except Exception as e:
            logger.error(f"解析索引失败: {seq_data}, error={e}")
            return 0


__all__ = ["NoticeSimulator", "SimulationState"]
