"""
简化的 Unitree B2 模拟器 - 仅用于 API 验证
不实现真实算法，只验证 API 调用和返回模拟响应
"""
from models import SystemState, FeedbackStatus, Feedback, Node, Edge, NavigationTask, CurrentPosition, TopologyMap
from typing import Dict, List
from datetime import datetime
import random
import math


class SimpleUnitreeSimulator:
    """简化模拟器 - 验证 API 格式"""

    def __init__(self):
        self.state = SystemState.IDLE
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.feedback_history: List[Feedback] = []
        self.tasks: Dict[str, NavigationTask] = {}  # 任务存储
        self.current_position = CurrentPosition(  # 模拟当前位置
            x=0.0, y=0.0, z=0.0, yaw=0.0,
            timestamp=datetime.now().isoformat()
        )
        self.last_waypoint: str = ""  # 最后记录的航点

    def _generate_seq(self) -> str:
        """生成命令序列号"""
        return str(random.randint(1, 10000))

    def _create_feedback(self, seq: str, success: bool, notice: str) -> Feedback:
        """生成标准反馈"""
        feedback = Feedback(
            index=seq,
            feedback=FeedbackStatus.SUCCESS if success else FeedbackStatus.FAILURE,
            state=self.state,
            notice=notice
        )
        self.feedback_history.append(feedback)
        return feedback

    # ========== SLAM 建图 ==========

    def start_mapping(self, seq: str) -> Feedback:
        """开始建图 (command: 3)"""
        self.state = SystemState.MAPPING
        return self._create_feedback(seq, True, "Mapping started successfully")

    def stop_mapping(self, seq: str) -> Feedback:
        """停止建图 (command: 4)"""
        self.state = SystemState.IDLE
        return self._create_feedback(seq, True, "Mapping stopped and map saved")

    # ========== 重定位 ==========

    def start_relocalization(self, seq: str) -> Feedback:
        """开始重定位 (command: 6)"""
        self.state = SystemState.RELOCATION_OPEN
        return self._create_feedback(seq, True, "Relocalization started")

    def init_relocalization(self, seq: str, x: float, y: float, yaw: float) -> Feedback:
        """重定位初始化 (command: 7)"""
        self.state = SystemState.LOCALIZATION_COMPLETE
        notice = f"Relocalization initialized at x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}"
        return self._create_feedback(seq, True, notice)

    # ========== 导航 ==========

    def start_navigation(self, seq: str) -> Feedback:
        """开始导航 (command: 8)"""
        self.state = SystemState.NAVIGATION_NODE_OPEN
        return self._create_feedback(seq, True, "Navigation started")

    def navigate_single_node(self, seq: str, node_name: str) -> Feedback:
        """单节点导航 (command: 9)"""
        if node_name not in self.nodes:
            return self._create_feedback(seq, False, f"Node '{node_name}' not found")

        self.state = SystemState.NAVIGATION
        notice = f"Navigating to node '{node_name}'"
        return self._create_feedback(seq, True, notice)

    def navigate_multi_loop(self, seq: str, node_names: List[str]) -> Feedback:
        """多节点循环导航 (command: 10)"""
        # 验证所有节点存在
        missing = [n for n in node_names if n not in self.nodes]
        if missing:
            return self._create_feedback(seq, False, f"Nodes not found: {missing}")

        self.state = SystemState.NAVIGATION
        notice = f"Multi-node loop navigation started with {len(node_names)} nodes"
        return self._create_feedback(seq, True, notice)

    def navigate_multi_once(self, seq: str, node_names: List[str]) -> Feedback:
        """多节点单次导航 (command: 11)"""
        missing = [n for n in node_names if n not in self.nodes]
        if missing:
            return self._create_feedback(seq, False, f"Nodes not found: {missing}")

        self.state = SystemState.NAVIGATION
        notice = f"Multi-node once navigation started with {len(node_names)} nodes"
        return self._create_feedback(seq, True, notice)

    def pause_navigation(self, seq: str) -> Feedback:
        """暂停导航 (command: 13)"""
        return self._create_feedback(seq, True, "Navigation paused")

    def resume_navigation(self, seq: str) -> Feedback:
        """恢复导航 (command: 14)"""
        return self._create_feedback(seq, True, "Navigation resumed")

    def return_to_start(self, seq: str) -> Feedback:
        """返回起始节点 (command: 15)"""
        return self._create_feedback(seq, True, "Returning to starting node")

    def stop_all(self, seq: str) -> Feedback:
        """停止所有功能 (command: 99)"""
        self.state = SystemState.IDLE
        return self._create_feedback(seq, True, "All nodes closed")

    # ========== 拓扑管理 ==========

    def add_node(self, seq: str, node: Node) -> Feedback:
        """添加节点"""
        if node.name in self.nodes:
            return self._create_feedback(seq, False, f"Node '{node.name}' already exists")

        self.nodes[node.name] = node
        notice = f"Node '{node.name}' added successfully"
        return self._create_feedback(seq, True, notice)

    def add_edge(self, seq: str, edge: Edge) -> Feedback:
        """添加边"""
        # 验证起点和终点节点存在
        if edge.start_node not in self.nodes:
            return self._create_feedback(seq, False, f"Start node '{edge.start_node}' not found")
        if edge.end_node not in self.nodes:
            return self._create_feedback(seq, False, f"End node '{edge.end_node}' not found")

        if edge.name in self.edges:
            return self._create_feedback(seq, False, f"Edge '{edge.name}' already exists")

        self.edges[edge.name] = edge
        notice = f"Edge '{edge.name}' added successfully"
        return self._create_feedback(seq, True, notice)

    def delete_item(self, seq: str, name: str) -> Feedback:
        """删除节点或边 (command: 1)"""
        if name in self.nodes:
            del self.nodes[name]
            # 同时删除相关的边
            edges_to_delete = [
                edge_name for edge_name, edge in self.edges.items()
                if edge.start_node == name or edge.end_node == name
            ]
            for edge_name in edges_to_delete:
                del self.edges[edge_name]

            notice = f"Node '{name}' and {len(edges_to_delete)} related edges deleted"
            return self._create_feedback(seq, True, notice)

        elif name in self.edges:
            del self.edges[name]
            return self._create_feedback(seq, True, f"Edge '{name}' deleted")

        else:
            return self._create_feedback(seq, False, f"Item '{name}' not found")

    def query_item(self, seq: str, name: str) -> dict:
        """查询节点或边 (command: 2)"""
        if name in self.nodes:
            feedback = self._create_feedback(seq, True, f"Node '{name}' found")
            return {
                "feedback": feedback,
                "type": "node",
                "data": self.nodes[name]
            }
        elif name in self.edges:
            feedback = self._create_feedback(seq, True, f"Edge '{name}' found")
            return {
                "feedback": feedback,
                "type": "edge",
                "data": self.edges[name]
            }
        else:
            feedback = self._create_feedback(seq, False, f"Item '{name}' not found")
            return {
                "feedback": feedback,
                "type": None,
                "data": None
            }

    # ========== 状态查询 ==========

    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "state": self.state,
            "state_name": self.state.name,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges)
        }

    def get_all_nodes(self) -> List[Node]:
        """获取所有节点"""
        return list(self.nodes.values())

    def get_all_edges(self) -> List[Edge]:
        """获取所有边"""
        return list(self.edges.values())

    def get_feedback_history(self, limit: int = 20) -> List[Feedback]:
        """获取反馈历史"""
        return self.feedback_history[-limit:]

    # ========== 实时位置 ==========

    def get_current_position(self) -> CurrentPosition:
        """获取当前实时位置"""
        # 模拟位置变化（在重定位后位置会更新）
        if self.state == SystemState.LOCALIZATION_COMPLETE or self.state == SystemState.NAVIGATION:
            # 添加少量随机漂移模拟实时更新
            self.current_position.x += random.uniform(-0.01, 0.01)
            self.current_position.y += random.uniform(-0.01, 0.01)
            self.current_position.yaw += random.uniform(-0.005, 0.005)
            self.current_position.timestamp = datetime.now().isoformat()

        return self.current_position

    def record_waypoint(self, seq: str, name: str) -> Feedback:
        """一键记录当前位置为航点"""
        if not name:
            return self._create_feedback(seq, False, "Waypoint name cannot be empty")

        if name in self.nodes:
            return self._create_feedback(seq, False, f"Waypoint '{name}' already exists")

        # 创建新节点（使用当前位置）
        node = Node(
            name=name,
            x=self.current_position.x,
            y=self.current_position.y,
            z=self.current_position.z,
            yaw=self.current_position.yaw
        )
        self.nodes[name] = node

        # 如果存在上一个航点，自动创建边
        if self.last_waypoint and self.last_waypoint in self.nodes:
            edge_name = f"{self.last_waypoint}_to_{name}"
            last_node = self.nodes[self.last_waypoint]

            # 计算欧氏距离
            distance = math.sqrt(
                (node.x - last_node.x)**2 +
                (node.y - last_node.y)**2 +
                (node.z - last_node.z)**2
            )

            edge = Edge(
                name=edge_name,
                start_node=self.last_waypoint,
                end_node=name,
                length=distance,
                speed=0.5
            )
            self.edges[edge_name] = edge

            notice = f"Waypoint '{name}' recorded and edge '{edge_name}' created (length: {distance:.2f}m)"
        else:
            notice = f"Waypoint '{name}' recorded at ({node.x:.2f}, {node.y:.2f})"

        self.last_waypoint = name
        return self._create_feedback(seq, True, notice)

    # ========== 拓扑地图文件操作 ==========

    def get_topology_map(self) -> TopologyMap:
        """获取完整拓扑地图"""
        return TopologyMap(
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            metadata={
                "created_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "edge_count": len(self.edges)
            }
        )

    def load_topology_map(self, seq: str, topo_map: TopologyMap) -> Feedback:
        """加载拓扑地图"""
        # 清空现有地图
        self.nodes.clear()
        self.edges.clear()

        # 加载新地图
        for node in topo_map.nodes:
            self.nodes[node.name] = node

        for edge in topo_map.edges:
            self.edges[edge.name] = edge

        notice = f"Topology map loaded: {len(topo_map.nodes)} nodes, {len(topo_map.edges)} edges"
        return self._create_feedback(seq, True, notice)

    def clear_topology_map(self, seq: str) -> Feedback:
        """清空拓扑地图"""
        node_count = len(self.nodes)
        edge_count = len(self.edges)

        self.nodes.clear()
        self.edges.clear()
        self.last_waypoint = ""

        notice = f"Topology map cleared: {node_count} nodes and {edge_count} edges removed"
        return self._create_feedback(seq, True, notice)

    # ========== 导航任务管理 ==========

    def create_task(self, task: NavigationTask) -> Feedback:
        """创建导航任务"""
        if task.id in self.tasks:
            seq = self._generate_seq()
            return self._create_feedback(seq, False, f"Task '{task.id}' already exists")

        # 验证所有节点存在
        missing = [n for n in task.node_names if n not in self.nodes]
        if missing:
            seq = self._generate_seq()
            return self._create_feedback(seq, False, f"Nodes not found: {missing}")

        self.tasks[task.id] = task
        seq = self._generate_seq()
        notice = f"Task '{task.name}' created with {len(task.node_names)} nodes"
        return self._create_feedback(seq, True, notice)

    def get_all_tasks(self) -> List[NavigationTask]:
        """获取所有任务"""
        return list(self.tasks.values())

    def get_task(self, task_id: str) -> NavigationTask | None:
        """获取指定任务"""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, task: NavigationTask) -> Feedback:
        """更新任务"""
        if task_id not in self.tasks:
            seq = self._generate_seq()
            return self._create_feedback(seq, False, f"Task '{task_id}' not found")

        # 验证所有节点存在
        missing = [n for n in task.node_names if n not in self.nodes]
        if missing:
            seq = self._generate_seq()
            return self._create_feedback(seq, False, f"Nodes not found: {missing}")

        task.updated_at = datetime.now().isoformat()
        self.tasks[task_id] = task
        seq = self._generate_seq()
        notice = f"Task '{task.name}' updated"
        return self._create_feedback(seq, True, notice)

    def delete_task(self, task_id: str) -> Feedback:
        """删除任务"""
        if task_id not in self.tasks:
            seq = self._generate_seq()
            return self._create_feedback(seq, False, f"Task '{task_id}' not found")

        task_name = self.tasks[task_id].name
        del self.tasks[task_id]
        seq = self._generate_seq()
        notice = f"Task '{task_name}' deleted"
        return self._create_feedback(seq, True, notice)

    def execute_task(self, seq: str, task_id: str) -> Feedback:
        """执行导航任务"""
        if task_id not in self.tasks:
            return self._create_feedback(seq, False, f"Task '{task_id}' not found")

        task = self.tasks[task_id]

        # 验证所有节点仍然存在
        missing = [n for n in task.node_names if n not in self.nodes]
        if missing:
            return self._create_feedback(seq, False, f"Nodes not found: {missing}")

        self.state = SystemState.NAVIGATION
        mode_text = "循环" if task.mode == "loop" else "单次"
        notice = f"Executing task '{task.name}' ({mode_text}) with {len(task.node_names)} nodes"
        return self._create_feedback(seq, True, notice)

