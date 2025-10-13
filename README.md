# Unitree B2 SLAM Web UI

Web界面控制 Unitree B2 机器人 SLAM 和导航功能。

## 项目结构

```
unitree-b2-slam-web/
├── backend/           # Python FastAPI 后端
│   ├── main.py       # FastAPI 应用
│   ├── simulator.py  # Unitree 模拟器
│   ├── models.py     # 数据模型
│   └── requirements.txt
├── frontend/         # React TypeScript 前端
└── docs/            # 文档
```

## 后端启动

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端将在 http://localhost:8000 启动
API 文档: http://localhost:8000/docs

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:5173 启动

## 功能特性

### 后端 API (17个接口)

**建图 (2个)**
- POST /api/mapping/start - 开始建图
- POST /api/mapping/stop - 停止建图

**重定位 (2个)**
- POST /api/reloc/start - 开始重定位
- POST /api/reloc/init - 初始化位姿

**导航 (9个)**
- POST /api/nav/start - 开始导航
- POST /api/nav/single - 单节点导航
- POST /api/nav/multi-loop - 多节点循环
- POST /api/nav/multi-once - 多节点单次
- POST /api/nav/pause - 暂停
- POST /api/nav/resume - 恢复
- POST /api/nav/return - 返回起点
- POST /api/nav/stop - 停止
- POST /api/nav/waypoints - 上传JSON文件

**拓扑 (4个)**
- POST /api/topo/node - 添加节点
- POST /api/topo/edge - 添加边
- DELETE /api/topo/{name} - 删除
- GET /api/topo/nodes - 查询所有节点
- GET /api/topo/edges - 查询所有边

**状态 (2个)**
- GET /api/status - 系统状态
- GET /api/feedback - 反馈历史

### 前端 UI (5个标签页)

1. **📍 建图** - SLAM 建图控制
2. **🎯 重定位** - 重定位和位姿初始化
3. **🚀 导航** - 单点/多点导航控制
4. **🗺️ 拓扑** - 拓扑节点和边管理
5. **📊 状态** - 系统状态和反馈监控

## 开发说明

### 第一阶段目标
- ✅ 完整的 Unitree SLAM API 模拟器
- ✅ 17个 REST API 接口
- ✅ 响应式前端界面（桌面+移动端）
- ✅ 完整的前后端交互

### 模拟器说明
当前模拟器仅用于 API 验证，不实现真实算法：
- ✅ 验证API参数格式
- ✅ 返回标准反馈消息
- ✅ 维护系统状态
- ❌ 不实现SLAM算法
- ❌ 不实现路径规划

## JSON 路点文件格式

```json
{
  "waypoints": [
    {
      "name": "point_1",
      "x": 1.0,
      "y": 2.0,
      "z": 0.0,
      "yaw": 0.0
    }
  ],
  "mode": "loop"
}
```

## License

MIT
