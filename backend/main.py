"""
FastAPI 后端服务 - Unitree B2 SLAM Web UI
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from simulator import SimpleUnitreeSimulator
from models import (
    Node, Edge, PoseInput, NavigationTarget, NavigationTargets,
    WaypointsFile, Feedback, NavigationTask, CurrentPosition, TopologyMap
)
import json
from typing import List

app = FastAPI(
    title="Unitree B2 SLAM Web API",
    description="Web API for controlling Unitree B2 SLAM and Navigation",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化模拟器
simulator = SimpleUnitreeSimulator()


# ==================== 建图接口 ====================

@app.post("/api/mapping/start", response_model=Feedback, tags=["Mapping"])
async def start_mapping():
    """开始 SLAM 建图 (Command: 3)"""
    seq = simulator._generate_seq()
    return simulator.start_mapping(seq)


@app.post("/api/mapping/stop", response_model=Feedback, tags=["Mapping"])
async def stop_mapping():
    """停止建图并保存地图 (Command: 4)"""
    seq = simulator._generate_seq()
    return simulator.stop_mapping(seq)


# ==================== 重定位接口 ====================

@app.post("/api/reloc/start", response_model=Feedback, tags=["Relocalization"])
async def start_relocalization():
    """开始重定位 (Command: 6)"""
    seq = simulator._generate_seq()
    return simulator.start_relocalization(seq)


@app.post("/api/reloc/init", response_model=Feedback, tags=["Relocalization"])
async def init_relocalization(pose: PoseInput):
    """重定位初始化 - 设置初始位姿 (Command: 7)"""
    seq = simulator._generate_seq()
    return simulator.init_relocalization(seq, pose.x, pose.y, pose.yaw)


# ==================== 导航接口 ====================

@app.post("/api/nav/start", response_model=Feedback, tags=["Navigation"])
async def start_navigation():
    """开始导航 (Command: 8)"""
    seq = simulator._generate_seq()
    return simulator.start_navigation(seq)


@app.post("/api/nav/single", response_model=Feedback, tags=["Navigation"])
async def navigate_single_node(target: NavigationTarget):
    """单节点导航 (Command: 9)"""
    seq = simulator._generate_seq()
    return simulator.navigate_single_node(seq, target.node_name)


@app.post("/api/nav/multi-loop", response_model=Feedback, tags=["Navigation"])
async def navigate_multi_loop(targets: NavigationTargets):
    """多节点循环导航 (Command: 10)"""
    seq = simulator._generate_seq()
    return simulator.navigate_multi_loop(seq, targets.node_names)


@app.post("/api/nav/multi-once", response_model=Feedback, tags=["Navigation"])
async def navigate_multi_once(targets: NavigationTargets):
    """多节点单次导航 (Command: 11)"""
    seq = simulator._generate_seq()
    return simulator.navigate_multi_once(seq, targets.node_names)


@app.post("/api/nav/pause", response_model=Feedback, tags=["Navigation"])
async def pause_navigation():
    """暂停导航 (Command: 13)"""
    seq = simulator._generate_seq()
    return simulator.pause_navigation(seq)


@app.post("/api/nav/resume", response_model=Feedback, tags=["Navigation"])
async def resume_navigation():
    """恢复导航 (Command: 14)"""
    seq = simulator._generate_seq()
    return simulator.resume_navigation(seq)


@app.post("/api/nav/return", response_model=Feedback, tags=["Navigation"])
async def return_to_start():
    """返回起始节点 (Command: 15)"""
    seq = simulator._generate_seq()
    return simulator.return_to_start(seq)


@app.post("/api/nav/stop", response_model=Feedback, tags=["Navigation"])
async def stop_all():
    """停止所有功能 (Command: 99)"""
    seq = simulator._generate_seq()
    return simulator.stop_all(seq)


@app.post("/api/nav/waypoints", response_model=Feedback, tags=["Navigation"])
async def upload_waypoints(file: UploadFile = File(...)):
    """
    上传 JSON 路点文件并导航

    JSON格式:
    {
        "waypoints": [
            {"name": "p1", "x": 1.0, "y": 2.0, "yaw": 0.0},
            ...
        ],
        "mode": "loop"
    }
    """
    try:
        content = await file.read()
        data = json.loads(content)
        waypoints_file = WaypointsFile(**data)

        # 先添加所有节点
        seq = simulator._generate_seq()
        for waypoint in waypoints_file.waypoints:
            simulator.add_node(simulator._generate_seq(), waypoint)

        # 然后开始导航
        node_names = [wp.name for wp in waypoints_file.waypoints]
        if waypoints_file.mode == "loop":
            return simulator.navigate_multi_loop(seq, node_names)
        else:
            return simulator.navigate_multi_once(seq, node_names)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 拓扑管理接口 ====================

@app.post("/api/topo/node", response_model=Feedback, tags=["Topology"])
async def add_node(node: Node):
    """添加拓扑节点"""
    seq = simulator._generate_seq()
    return simulator.add_node(seq, node)


@app.post("/api/topo/edge", response_model=Feedback, tags=["Topology"])
async def add_edge(edge: Edge):
    """添加拓扑边"""
    seq = simulator._generate_seq()
    return simulator.add_edge(seq, edge)


@app.delete("/api/topo/{name}", response_model=Feedback, tags=["Topology"])
async def delete_item(name: str):
    """删除节点或边 (Command: 1)"""
    seq = simulator._generate_seq()
    return simulator.delete_item(seq, name)


@app.get("/api/topo/query/{name}", tags=["Topology"])
async def query_item(name: str):
    """查询节点或边 (Command: 2)"""
    seq = simulator._generate_seq()
    return simulator.query_item(seq, name)


@app.get("/api/topo/nodes", response_model=List[Node], tags=["Topology"])
async def get_all_nodes():
    """获取所有节点"""
    return simulator.get_all_nodes()


@app.get("/api/topo/edges", response_model=List[Edge], tags=["Topology"])
async def get_all_edges():
    """获取所有边"""
    return simulator.get_all_edges()


# ==================== 状态查询接口 ====================

@app.get("/api/status", tags=["Status"])
async def get_status():
    """获取系统状态"""
    return simulator.get_status()


@app.get("/api/feedback", response_model=List[Feedback], tags=["Status"])
async def get_feedback_history(limit: int = 20):
    """获取反馈历史"""
    return simulator.get_feedback_history(limit)


# ==================== 实时位置接口 ====================

@app.get("/api/position/current", response_model=CurrentPosition, tags=["Position"])
async def get_current_position():
    """获取当前实时位置"""
    return simulator.get_current_position()


@app.post("/api/position/record-waypoint", response_model=Feedback, tags=["Position"])
async def record_waypoint(name: str):
    """一键记录当前位置为航点"""
    seq = simulator._generate_seq()
    return simulator.record_waypoint(seq, name)


# ==================== 拓扑地图文件操作 ====================

@app.get("/api/topo/map", response_model=TopologyMap, tags=["Topology"])
async def get_topology_map():
    """获取完整拓扑地图（用于保存）"""
    return simulator.get_topology_map()


@app.post("/api/topo/map/load", response_model=Feedback, tags=["Topology"])
async def load_topology_map(topo_map: TopologyMap):
    """加载拓扑地图"""
    seq = simulator._generate_seq()
    return simulator.load_topology_map(seq, topo_map)


@app.post("/api/topo/map/clear", response_model=Feedback, tags=["Topology"])
async def clear_topology_map():
    """清空拓扑地图"""
    seq = simulator._generate_seq()
    return simulator.clear_topology_map(seq)


# ==================== 导航任务管理接口 ====================

@app.post("/api/task/create", response_model=Feedback, tags=["Task"])
async def create_task(task: NavigationTask):
    """创建导航任务"""
    return simulator.create_task(task)


@app.get("/api/task/list", response_model=List[NavigationTask], tags=["Task"])
async def get_all_tasks():
    """获取所有导航任务"""
    return simulator.get_all_tasks()


@app.get("/api/task/{task_id}", response_model=NavigationTask, tags=["Task"])
async def get_task(task_id: str):
    """获取指定任务详情"""
    task = simulator.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@app.put("/api/task/{task_id}", response_model=Feedback, tags=["Task"])
async def update_task(task_id: str, task: NavigationTask):
    """更新导航任务"""
    return simulator.update_task(task_id, task)


@app.delete("/api/task/{task_id}", response_model=Feedback, tags=["Task"])
async def delete_task(task_id: str):
    """删除导航任务"""
    return simulator.delete_task(task_id)


@app.post("/api/task/{task_id}/execute", response_model=Feedback, tags=["Task"])
async def execute_task(task_id: str):
    """执行导航任务"""
    seq = simulator._generate_seq()
    return simulator.execute_task(seq, task_id)


@app.get("/", tags=["Root"])
async def root():
    """API 根路径"""
    return {
        "message": "Unitree B2 SLAM Web API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "simulator": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
