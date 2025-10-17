"""
SLAM 服务核心

封装 Unitree SLAM 功能，提供面向 FastAPI 的接口
"""

import asyncio
from typing import List, Optional, Callable
from threading import Thread, Lock
from abc import ABC, abstractmethod

from config import config
from logger import get_logger
from slam.message_types import (
    QtCommand_,
    QtNode_,
    QtEdge_,
    Odometry_,
    String_,
    NodeAttribute,
    EdgeAttribute,
    QtNotice,
    SystemState,
)
from slam.command_builder import CommandBuilder, yaw_from_quaternion
from slam.command_executor import CommandExecutor, CommandRecord, CommandStatus

logger = get_logger("slam_service")


# ============ 通信适配器（Adapter Pattern）============

class MessageAdapter(ABC):
    """消息适配器抽象基类

    封装不同通信方式（DDS、仿真器等）的差异，
    为 Publisher/Subscriber 提供统一接口
    """

    def __init__(self, topic: str, message_type):
        self.topic = topic
        self.message_type = message_type

    @abstractmethod
    def init_publisher(self):
        """初始化发布器"""
        pass

    @abstractmethod
    def init_subscriber(self, callback: Callable, queue_size: int = 10):
        """初始化订阅器"""
        pass

    @abstractmethod
    def publish(self, msg):
        """发布消息"""
        pass


class DDSAdapter(MessageAdapter):
    """DDS 通信适配器（真实硬件）

    封装 Unitree SDK 的 DDS 通信
    """

    def __init__(self, topic: str, message_type):
        super().__init__(topic, message_type)

        # 延迟导入，避免在仿真模式下依赖 SDK
        from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
        self._channel_publisher = ChannelPublisher(topic, message_type)
        self._channel_subscriber = ChannelSubscriber(topic, message_type)

    def init_publisher(self):
        """初始化 DDS 发布器"""
        self._channel_publisher.Init()
        logger.debug(f"DDS Publisher 初始化: {self.topic}")

    def init_subscriber(self, callback: Callable, queue_size: int = 10):
        """初始化 DDS 订阅器"""
        self._channel_subscriber.Init(callback, queue_size)
        logger.debug(f"DDS Subscriber 初始化: {self.topic}")

    def publish(self, msg):
        """通过 DDS 发布消息"""
        self._channel_publisher.Write(msg)


class SimulatorAdapter(MessageAdapter):
    """仿真器通信适配器

    封装仿真器的消息处理
    """

    def __init__(self, topic: str, message_type, simulator=None):
        super().__init__(topic, message_type)
        self._simulator = simulator
        self._callback: Optional[Callable] = None

    def set_simulator(self, simulator):
        """设置仿真器实例"""
        self._simulator = simulator

    def init_publisher(self):
        """初始化仿真发布器（无需特殊初始化）"""
        logger.debug(f"Simulator Publisher 初始化: {self.topic}")

    def init_subscriber(self, callback: Callable, queue_size: int = 10):
        """初始化仿真订阅器"""
        self._callback = callback
        logger.debug(f"Simulator Subscriber 初始化: {self.topic}")

    def publish(self, msg):
        """发布消息到仿真器"""
        logger.debug(f"Simulator 发布消息: {self.topic}")

        if not self._simulator:
            logger.warning(f"仿真器未设置，无法发布消息: {self.topic}")
            return

        # 根据消息类型路由到仿真器的不同处理方法
        if self.message_type == QtCommand_:
            asyncio.create_task(self._simulator.handle_command(msg))
        elif self.message_type == QtNode_:
            asyncio.create_task(self._simulator.handle_save_nodes(msg))
        elif self.message_type == QtEdge_:
            asyncio.create_task(self._simulator.handle_save_edges(msg))
        else:
            logger.warning(f"未知的仿真消息类型: {self.message_type}")

    def trigger_callback(self, msg):
        """触发订阅回调（仿真模式下由仿真器调用）"""
        if self._callback:
            self._callback(msg)


# ============ 统一的 Publisher/Subscriber ============

class Publisher:
    """统一的发布器

    使用适配器模式，支持多种通信方式
    """

    def __init__(self, adapter: MessageAdapter):
        self._adapter = adapter
        self.topic = adapter.topic
        self.message_type = adapter.message_type

    def init(self):
        """初始化发布器"""
        self._adapter.init_publisher()

    def write(self, msg):
        """发布消息"""
        self._adapter.publish(msg)

    def get_adapter(self) -> MessageAdapter:
        """获取适配器（用于特殊操作）"""
        return self._adapter


class Subscriber:
    """统一的订阅器

    使用适配器模式，支持多种通信方式
    """

    def __init__(self, adapter: MessageAdapter):
        self._adapter = adapter
        self.topic = adapter.topic
        self.message_type = adapter.message_type

    def init(self, callback: Callable, queue_size: int = 10):
        """初始化订阅器"""
        self._adapter.init_subscriber(callback, queue_size)

    def get_adapter(self) -> MessageAdapter:
        """获取适配器（用于特殊操作）"""
        return self._adapter


# ============ SLAM 服务主类 ============

class SlamService:
    """SLAM 服务核心类"""

    def __init__(
        self,
        simulator_mode: bool = None,
        network_interface: Optional[str] = None,
    ):
        """
        初始化 SLAM 服务

        Args:
            simulator_mode: 是否使用仿真模式（None 则使用配置）
            network_interface: 网络接口名称（仅真实模式）
        """
        self.simulator_mode = simulator_mode if simulator_mode is not None else config.SIMULATOR_MODE
        self.network_interface = network_interface or config.NETWORK_INTERFACE

        # 状态变量
        self._current_odom: Optional[Odometry_] = None
        self._current_odom_lock = Lock()
        self._system_state: SystemState = SystemState.IDLE
        self._state_lock = Lock()

        # 节点和边的临时存储（用于拓扑图构建）
        self._node_counter = 0
        self._node_list: List[NodeAttribute] = []
        self._edge_list: List[EdgeAttribute] = []
        self._topology_lock = Lock()

        # 回调函数
        self._notice_callbacks: List[Callable] = []
        self._odom_callbacks: List[Callable] = []

        # 初始化命令执行器
        self._executor = CommandExecutor(
            start_index=1,
            end_index=10000,
            timeout=config.COMMAND_TIMEOUT,
        )

        # 初始化命令构建器
        self._builder = CommandBuilder(self._executor.get_next_index)

        # 初始化发布器和订阅器
        self._init_communication()

        logger.info(
            f"SlamService 初始化: "
            f"simulator_mode={self.simulator_mode}, "
            f"network_interface={self.network_interface}"
        )

    def _init_communication(self):
        """初始化通信组件"""
        if self.simulator_mode:
            # 仿真模式
            logger.info("使用仿真模式")

            # 创建仿真管理器
            from simulator import get_simulator_manager
            self._simulator = get_simulator_manager()

            # 创建仿真适配器
            adapter_command = SimulatorAdapter(config.TOPIC_QT_COMMAND, QtCommand_, self._simulator)
            adapter_node = SimulatorAdapter(config.TOPIC_ADD_NODE, QtNode_, self._simulator)
            adapter_edge = SimulatorAdapter(config.TOPIC_ADD_EDGE, QtEdge_, self._simulator)
            adapter_notice = SimulatorAdapter(config.TOPIC_QT_NOTICE, String_)
            adapter_odom = SimulatorAdapter(config.TOPIC_ODOM, Odometry_)

            # 创建统一的 Publisher/Subscriber
            self.pub_command = Publisher(adapter_command)
            self.pub_node = Publisher(adapter_node)
            self.pub_edge = Publisher(adapter_edge)
            self.sub_notice = Subscriber(adapter_notice)
            self.sub_odom = Subscriber(adapter_odom)

        else:
            # 真实模式
            logger.info("使用真实模式")

            self._simulator = None

            # 初始化 DDS
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize
            if self.network_interface:
                ChannelFactoryInitialize(0, self.network_interface)
                logger.info(f"DDS 初始化: network_interface={self.network_interface}")
            else:
                ChannelFactoryInitialize(0)
                logger.info("DDS 初始化: 使用默认网络接口")

            # 创建 DDS 适配器
            adapter_command = DDSAdapter(config.TOPIC_QT_COMMAND, QtCommand_)
            adapter_node = DDSAdapter(config.TOPIC_ADD_NODE, QtNode_)
            adapter_edge = DDSAdapter(config.TOPIC_ADD_EDGE, QtEdge_)
            adapter_notice = DDSAdapter(config.TOPIC_QT_NOTICE, String_)
            adapter_odom = DDSAdapter(config.TOPIC_ODOM, Odometry_)

            # 创建统一的 Publisher/Subscriber
            self.pub_command = Publisher(adapter_command)
            self.pub_node = Publisher(adapter_node)
            self.pub_edge = Publisher(adapter_edge)
            self.sub_notice = Subscriber(adapter_notice)
            self.sub_odom = Subscriber(adapter_odom)

        # 初始化所有发布器
        self.pub_command.init()
        self.pub_node.init()
        self.pub_edge.init()

        # 初始化所有订阅器
        self.sub_notice.init(self._qt_notice_handler, 10)
        self.sub_odom.init(self._odometry_handler, 1)

        # 如果是仿真模式，连接仿真器回调
        if self.simulator_mode and self._simulator:
            # 获取仿真适配器并设置回调
            notice_adapter = self.sub_notice.get_adapter()
            odom_adapter = self.sub_odom.get_adapter()

            if isinstance(notice_adapter, SimulatorAdapter):
                self._simulator.set_notice_callback(lambda msg: notice_adapter.trigger_callback(msg))

            if isinstance(odom_adapter, SimulatorAdapter):
                self._simulator.set_odom_callback(lambda msg: odom_adapter.trigger_callback(msg))

            # 启动仿真器（异步）
            asyncio.create_task(self._simulator.start())
            logger.info("仿真器已连接并启动")

    # ============ 回调处理 ============

    def _odometry_handler(self, msg: Odometry_):
        """里程计消息回调"""
        with self._current_odom_lock:
            self._current_odom = msg

        # 触发用户注册的回调
        for callback in self._odom_callbacks:
            try:
                callback(msg)
            except Exception as e:
                logger.error(f"里程计回调执行失败: {e}")

    def _qt_notice_handler(self, msg: String_):
        """Qt Notice 消息回调"""
        data = msg.data
        logger.debug(f"收到 qt_notice: {data}")

        # 解析 notice
        try:
            qt_notice = QtNotice.parse(data)
        except Exception as e:
            logger.error(f"解析 qt_notice 失败: {e}, data={data}")
            return

        # 更新系统状态
        if qt_notice.state is not None:
            try:
                with self._state_lock:
                    self._system_state = SystemState(qt_notice.state)
                logger.info(f"系统状态更新: {self._system_state.name}")
            except ValueError:
                logger.warning(f"未知系统状态: {qt_notice.state}")

        # 处理命令反馈
        if qt_notice.feedback is not None:
            self._executor.handle_feedback(qt_notice)

        # 触发用户注册的回调
        for callback in self._notice_callbacks:
            try:
                callback(qt_notice)
            except Exception as e:
                logger.error(f"Notice 回调执行失败: {e}")

    def register_notice_callback(self, callback: Callable[[QtNotice], None]):
        """注册 qt_notice 回调"""
        self._notice_callbacks.append(callback)
        logger.debug(f"注册 notice 回调: {callback.__name__}")

    def register_odom_callback(self, callback: Callable[[Odometry_], None]):
        """注册里程计回调"""
        self._odom_callbacks.append(callback)
        logger.debug(f"注册里程计回调: {callback.__name__}")

    # ============ 状态查询 ============

    def get_current_odom(self) -> Optional[Odometry_]:
        """获取当前里程计数据"""
        with self._current_odom_lock:
            return self._current_odom

    def get_system_state(self) -> SystemState:
        """获取当前系统状态"""
        with self._state_lock:
            return self._system_state

    # ============ 建图操作 ============

    async def start_mapping(self) -> CommandRecord:
        """
        开始建图

        Returns:
            命令执行记录
        """
        logger.info("开始建图")

        index, cmd = self._builder.build_start_mapping()
        self._executor.register_command(index, "START_MAPPING")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def end_mapping(self, pcdmap_index: int, save: bool = True) -> CommandRecord:
        """
        结束建图

        Args:
            pcdmap_index: PCD 地图索引
            save: 是否保存地图

        Returns:
            命令执行记录
        """
        logger.info(f"结束建图: pcdmap_index={pcdmap_index}, save={save}")

        index, cmd = self._builder.build_end_mapping(pcdmap_index, save=save)
        self._executor.register_command(index, "END_MAPPING")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    # ============ 重定位操作 ============

    async def start_relocation(self) -> CommandRecord:
        """
        开启重定位

        Returns:
            命令执行记录
        """
        logger.info("开启重定位")

        index, cmd = self._builder.build_start_relocation()
        self._executor.register_command(index, "START_RELOCATION")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def init_pose(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        qx: float = 0.0,
        qy: float = 0.0,
        qz: float = 0.0,
        qw: float = 1.0,
    ) -> CommandRecord:
        """
        初始化位姿

        Args:
            x, y, z: 位置坐标
            qx, qy, qz, qw: 四元数

        Returns:
            命令执行记录
        """
        logger.info(f"初始化位姿: pos=({x}, {y}, {z}), quat=({qx}, {qy}, {qz}, {qw})")

        index, cmd = self._builder.build_init_pose(x, y, z, qx, qy, qz, qw)
        self._executor.register_command(index, "INIT_POSE")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    # ============ 导航操作 ============

    async def start_navigation(self) -> CommandRecord:
        """
        开启导航

        Returns:
            命令执行记录
        """
        logger.info("开启导航")

        index, cmd = self._builder.build_start_navigation()
        self._executor.register_command(index, "START_NAVIGATION")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def single_point_nav(self, target_node: int) -> CommandRecord:
        """
        单点导航

        Args:
            target_node: 目标节点 ID

        Returns:
            命令执行记录
        """
        logger.info(f"单点导航: target={target_node}")

        index, cmd = self._builder.build_single_point_nav(target_node)
        self._executor.register_command(index, "SINGLE_POINT_NAV")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def loop_navigation(
        self, node_sequence: Optional[List[int]] = None
    ) -> CommandRecord:
        """
        多点循环导航

        Args:
            node_sequence: 节点序列（None 表示默认循环）

        Returns:
            命令执行记录
        """
        if node_sequence:
            logger.info(f"自定义循环导航: sequence={node_sequence}")
        else:
            logger.info("默认循环导航")

        index, cmd = self._builder.build_loop_navigation(node_sequence)
        self._executor.register_command(
            index, "LOOP_NAV_CUSTOM" if node_sequence else "LOOP_NAV_DEFAULT"
        )
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def pause_navigation(self) -> CommandRecord:
        """暂停导航"""
        logger.info("暂停导航")

        index, cmd = self._builder.build_pause_navigation()
        self._executor.register_command(index, "PAUSE_NAV")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def resume_navigation(self) -> CommandRecord:
        """恢复导航"""
        logger.info("恢复导航")

        index, cmd = self._builder.build_resume_navigation()
        self._executor.register_command(index, "RESUME_NAV")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def return_home(self) -> CommandRecord:
        """返回起点"""
        logger.info("返回起点")

        index, cmd = self._builder.build_return_home()
        self._executor.register_command(index, "RETURN_HOME")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    # ============ 拓扑图操作 ============

    def add_node_from_odom(self) -> Optional[NodeAttribute]:
        """
        基于当前里程计添加节点

        Returns:
            添加的节点，如果没有里程计数据则返回 None
        """
        odom = self.get_current_odom()
        if odom is None:
            logger.warning("无法添加节点: 没有里程计数据")
            return None

        # 提取位姿
        pose = odom.pose.pose
        x = pose.position.x
        y = pose.position.y
        z = pose.position.z

        qx = pose.orientation.x
        qy = pose.orientation.y
        qz = pose.orientation.z
        qw = pose.orientation.w

        yaw = yaw_from_quaternion(qx, qy, qz, qw)

        with self._topology_lock:
            self._node_counter += 1
            node = NodeAttribute(
                node_name=self._node_counter,
                node_x=x,
                node_y=y,
                node_z=z,
                node_yaw=yaw,
            )
            self._node_list.append(node)

            # 自动连接到前一个节点
            if self._node_counter >= 2:
                edge = EdgeAttribute(
                    edge_name=self._node_counter - 1,
                    edge_start=self._node_counter - 1,
                    edge_end=self._node_counter,
                )
                self._edge_list.append(edge)
                logger.info(
                    f"添加边: {edge.edge_name} ({edge.edge_start} -> {edge.edge_end})"
                )

        logger.info(f"添加节点: {node.node_name}, pos=({x:.3f}, {y:.3f}, {z:.3f}), yaw={yaw:.3f}")
        return node

    async def save_topology(self) -> tuple[CommandRecord, CommandRecord]:
        """
        保存拓扑图（节点和边）

        Returns:
            (节点命令记录, 边命令记录)
        """
        with self._topology_lock:
            if not self._edge_list:
                raise ValueError("拓扑图为空，至少需要 2 个节点")

            nodes = list(self._node_list)
            edges = list(self._edge_list)

        logger.info(f"保存拓扑图: {len(nodes)} 个节点, {len(edges)} 条边")

        # 保存节点
        index_node, qt_node = self._builder.build_save_nodes(nodes)
        self._executor.register_command(index_node, "SAVE_NODES")
        self.pub_node.write(qt_node)

        # 保存边
        index_edge, qt_edge = self._builder.build_save_edges(edges)
        self._executor.register_command(index_edge, "SAVE_EDGES")
        self.pub_edge.write(qt_edge)

        # 等待两个命令完成
        record_node = await self._executor.wait_for_command(index_node)
        record_edge = await self._executor.wait_for_command(index_edge)

        return record_node, record_edge

    def clear_topology(self):
        """清除本地拓扑图缓存"""
        with self._topology_lock:
            self._node_list.clear()
            self._edge_list.clear()
            self._node_counter = 0

        logger.info("已清除本地拓扑图缓存")

    def get_topology_summary(self) -> dict:
        """获取拓扑图摘要"""
        with self._topology_lock:
            return {
                "node_count": len(self._node_list),
                "edge_count": len(self._edge_list),
                "nodes": [
                    {
                        "name": node.node_name,
                        "x": node.node_x,
                        "y": node.node_y,
                        "z": node.node_z,
                        "yaw": node.node_yaw,
                    }
                    for node in self._node_list
                ],
                "edges": [
                    {
                        "name": edge.edge_name,
                        "start": edge.edge_start,
                        "end": edge.edge_end,
                    }
                    for edge in self._edge_list
                ],
            }

    async def delete_nodes(self, node_ids: Optional[List[int]] = None) -> CommandRecord:
        """
        删除节点

        Args:
            node_ids: 要删除的节点 ID 列表（None 表示删除全部）

        Returns:
            命令执行记录
        """
        if node_ids:
            logger.info(f"删除节点: {node_ids}")
        else:
            logger.info("删除所有节点")

        index, cmd = self._builder.build_delete_nodes(node_ids)
        self._executor.register_command(index, "DELETE_NODES")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    async def delete_edges(self, edge_ids: Optional[List[int]] = None) -> CommandRecord:
        """
        删除边

        Args:
            edge_ids: 要删除的边 ID 列表（None 表示删除全部）

        Returns:
            命令执行记录
        """
        if edge_ids:
            logger.info(f"删除边: {edge_ids}")
        else:
            logger.info("删除所有边")

        index, cmd = self._builder.build_delete_edges(edge_ids)
        self._executor.register_command(index, "DELETE_EDGES")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    # ============ 系统操作 ============

    async def close_all(self) -> CommandRecord:
        """关闭所有节点"""
        logger.info("关闭所有节点")

        index, cmd = self._builder.build_close_all()
        self._executor.register_command(index, "CLOSE_ALL")
        self.pub_command.write(cmd)

        return await self._executor.wait_for_command(index)

    # ============ 维护操作 ============

    def get_command_statistics(self) -> dict:
        """获取命令执行统计"""
        return self._executor.get_statistics()

    def check_command_timeout(self):
        """检查超时命令"""
        self._executor.check_timeout()

    def clear_old_commands(self, max_age: float = 300):
        """清理旧命令记录"""
        self._executor.clear_old_commands(max_age)


# ============ 全局单例 ============

_slam_service: Optional[SlamService] = None
_slam_service_lock = Lock()


def get_slam_service() -> SlamService:
    """获取全局 SLAM 服务实例"""
    global _slam_service

    with _slam_service_lock:
        if _slam_service is None:
            _slam_service = SlamService()

    return _slam_service


def initialize_slam_service(
    simulator_mode: bool = None,
    network_interface: Optional[str] = None,
) -> SlamService:
    """
    初始化全局 SLAM 服务实例

    Args:
        simulator_mode: 是否使用仿真模式
        network_interface: 网络接口名称

    Returns:
        SLAM 服务实例
    """
    global _slam_service

    with _slam_service_lock:
        if _slam_service is not None:
            logger.warning("SlamService 已初始化，将重新创建")

        _slam_service = SlamService(simulator_mode, network_interface)

    return _slam_service


__all__ = [
    "SlamService",
    "get_slam_service",
    "initialize_slam_service",
    "Publisher",
    "Subscriber",
    "MessageAdapter",
    "DDSAdapter",
    "SimulatorAdapter",
]
