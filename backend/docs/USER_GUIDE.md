# Unitree B2 SLAM Backend - 用户指南

## 📖 目录

- [快速开始](#快速开始)
- [API 使用指南](#api-使用指南)
  - [建图操作](#建图操作)
  - [重定位操作](#重定位操作)
  - [导航操作](#导航操作)
  - [拓扑图管理](#拓扑图管理)
  - [状态查询](#状态查询)
  - [地图管理](#地图管理)
- [WebSocket 实时推送](#websocket-实时推送)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [故障排查](#故障排查)

---

## 快速开始

### 1. 环境要求

- **Python**: 3.10+
- **操作系统**: Linux / macOS / Windows (WSL)
- **硬件**:
  - 仿真模式: 无特殊要求
  - 真实模式: Unitree B2 机器人 + DDS 网络连接

### 2. 安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd unitree-b2-slam-web/backend

# 2. 运行安装脚本
bash setup.sh

# 3. 激活虚拟环境
source .venv/bin/activate
```

### 3. 配置

复制环境变量模板并根据需要修改：

```bash
cp .env.example .env
# 编辑 .env 文件
```

重要配置项：

```bash
# 运行模式
SIMULATOR_MODE=true          # true=仿真模式, false=真实硬件

# 服务配置
HOST=0.0.0.0
PORT=8000

# 网络接口（真实模式）
NETWORK_INTERFACE=eth0       # 根据实际网络接口修改
```

### 4. 运行服务

```bash
# 仿真模式（推荐用于开发和测试）
make run-sim

# 或使用 Python 直接运行
SIMULATOR_MODE=true python main.py

# 真实模式（需要连接 Unitree B2）
make run
```

### 5. 访问 API 文档

服务启动后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## API 使用指南

所有 API 遵循统一的响应格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

### 建图操作

#### 1. 开始建图

```bash
curl -X POST http://localhost:8000/api/mapping/start
```

**响应示例**：
```json
{
  "success": true,
  "message": "开始建图成功",
  "data": {
    "index": 1,
    "status": "success",
    "response_time": 0.501
  }
}
```

#### 2. 结束建图

```bash
curl -X POST http://localhost:8000/api/mapping/end \
  -H "Content-Type: application/json" \
  -d '{
    "pcdmap_index": 1,
    "save_map": true
  }'
```

**参数说明**：
- `pcdmap_index`: 地图索引号（整数）
- `save_map`: 是否保存地图（true/false）

**完整建图流程**：
```bash
# 1. 开始建图
curl -X POST http://localhost:8000/api/mapping/start

# 2. 机器人移动，收集环境数据（由用户控制）

# 3. 添加拓扑节点（可选）
curl -X POST http://localhost:8000/api/topology/add_node

# 4. 保存拓扑图（可选）
curl -X POST http://localhost:8000/api/topology/save

# 5. 结束建图并保存
curl -X POST http://localhost:8000/api/mapping/end \
  -H "Content-Type: application/json" \
  -d '{"pcdmap_index": 1, "save_map": true}'
```

---

### 重定位操作

#### 1. 开启重定位

```bash
curl -X POST http://localhost:8000/api/relocation/start
```

#### 2. 初始化位姿

```bash
curl -X POST http://localhost:8000/api/relocation/init_pose \
  -H "Content-Type: application/json" \
  -d '{
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "qx": 0.0,
    "qy": 0.0,
    "qz": 0.0,
    "qw": 1.0
  }'
```

**参数说明**：
- `x, y, z`: 位置坐标（米）
- `qx, qy, qz, qw`: 姿态四元数

**重定位流程**：
```bash
# 1. 开启重定位
curl -X POST http://localhost:8000/api/relocation/start

# 2. 等待系统重定位完成，或手动初始化位姿
curl -X POST http://localhost:8000/api/relocation/init_pose \
  -H "Content-Type: application/json" \
  -d '{"x": 0.0, "y": 0.0, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}'

# 3. 检查系统状态
curl http://localhost:8000/api/status/system
```

---

### 导航操作

#### 1. 开启导航

```bash
curl -X POST http://localhost:8000/api/navigation/start
```

#### 2. 单点导航

```bash
curl -X POST http://localhost:8000/api/navigation/single_point \
  -H "Content-Type: application/json" \
  -d '{"target_node": 5}'
```

#### 3. 循环导航

```bash
# 自定义路径
curl -X POST http://localhost:8000/api/navigation/loop \
  -H "Content-Type: application/json" \
  -d '{"node_sequence": [1, 2, 3, 4]}'

# 默认循环（所有节点）
curl -X POST http://localhost:8000/api/navigation/loop \
  -H "Content-Type: application/json" \
  -d '{"node_sequence": null}'
```

#### 4. 暂停/恢复导航

```bash
# 暂停
curl -X POST http://localhost:8000/api/navigation/pause

# 恢复
curl -X POST http://localhost:8000/api/navigation/resume
```

#### 5. 返回起点

```bash
curl -X POST http://localhost:8000/api/navigation/return_home
```

**完整导航流程**：
```bash
# 1. 开启重定位
curl -X POST http://localhost:8000/api/relocation/start
sleep 1

# 2. 初始化位姿
curl -X POST http://localhost:8000/api/relocation/init_pose \
  -H "Content-Type: application/json" \
  -d '{"x": 0.0, "y": 0.0, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}'
sleep 1

# 3. 开启导航
curl -X POST http://localhost:8000/api/navigation/start
sleep 1

# 4. 单点导航
curl -X POST http://localhost:8000/api/navigation/single_point \
  -H "Content-Type: application/json" \
  -d '{"target_node": 3}'
```

---

### 拓扑图管理

#### 1. 添加节点

基于当前机器人位姿添加拓扑节点：

```bash
curl -X POST http://localhost:8000/api/topology/add_node
```

**响应示例**：
```json
{
  "success": true,
  "message": "节点添加成功",
  "data": {
    "node": {
      "name": 1,
      "x": 1.234,
      "y": 2.345,
      "z": 0.0,
      "yaw": 0.785
    }
  }
}
```

#### 2. 保存拓扑图

将本地拓扑图保存到 SLAM 系统：

```bash
curl -X POST http://localhost:8000/api/topology/save
```

#### 3. 查询拓扑图摘要

```bash
curl http://localhost:8000/api/topology/summary
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "node_count": 5,
    "edge_count": 4,
    "nodes": [
      {"name": 1, "x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0},
      {"name": 2, "x": 1.0, "y": 0.0, "z": 0.0, "yaw": 0.0}
    ],
    "edges": [
      {"name": 1, "start": 1, "end": 2}
    ]
  }
}
```

#### 4. 删除节点

```bash
# 删除指定节点
curl -X DELETE http://localhost:8000/api/topology/nodes \
  -H "Content-Type: application/json" \
  -d '{"node_ids": [1, 2, 3]}'

# 删除所有节点
curl -X DELETE http://localhost:8000/api/topology/nodes \
  -H "Content-Type: application/json" \
  -d '{"node_ids": null}'
```

#### 5. 删除边

```bash
# 删除指定边
curl -X DELETE http://localhost:8000/api/topology/edges \
  -H "Content-Type: application/json" \
  -d '{"edge_ids": [1, 2]}'

# 删除所有边
curl -X DELETE http://localhost:8000/api/topology/edges \
  -H "Content-Type: application/json" \
  -d '{"edge_ids": null}'
```

#### 6. 清除本地缓存

```bash
curl -X POST http://localhost:8000/api/topology/clear
```

---

### 状态查询

#### 1. 查询系统状态

```bash
curl http://localhost:8000/api/status/system
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "state": 3,
    "state_name": "NAVIGATION"
  }
}
```

**状态码说明**:
- `-1`: ERROR - 错误
- `0`: IDLE - 空闲
- `2`: MAPPING - 建图中
- `3`: NAVIGATION - 导航中
- `4`: RELOCATION - 重定位开启
- `5`: INIT_POSE - 初始化定位完成
- `6`: NAV_NODE_OPEN - 导航节点打开

#### 2. 查询里程计数据

```bash
curl http://localhost:8000/api/status/odometry
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "position": {
      "x": 1.234,
      "y": 2.345,
      "z": 0.001
    },
    "orientation": {
      "x": 0.0,
      "y": 0.0,
      "z": 0.383,
      "w": 0.924
    }
  }
}
```

#### 3. 查询命令统计

```bash
curl http://localhost:8000/api/status/commands
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 15,
    "pending": 0,
    "sent": 1,
    "success": 13,
    "failed": 0,
    "timeout": 1
  }
}
```

---

### 地图管理

#### 1. 获取地图列表

```bash
curl http://localhost:8000/api/maps
```

#### 2. 创建地图记录

```bash
curl -X POST http://localhost:8000/api/maps \
  -H "Content-Type: application/json" \
  -d '{"map_name": "office_floor1"}'
```

#### 3. 删除地图记录

```bash
curl -X DELETE http://localhost:8000/api/maps/1
```

---

## WebSocket 实时推送

WebSocket 提供实时数据推送功能。

### 连接方式

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket 已连接');

  // 订阅主题
  ws.send(JSON.stringify({
    action: 'subscribe',
    topics: ['qt_notice', 'odometry', 'system_status']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};
```

### 支持的主题

1. **qt_notice** - Qt Notice 消息
   ```json
   {
     "type": "qt_notice",
     "data": {
       "index": 1,
       "feedback": 1,
       "state": 2,
       "notice": "建图已开始"
     }
   }
   ```

2. **odometry** - 里程计数据（10Hz）
   ```json
   {
     "type": "odometry",
     "data": {
       "position": {"x": 1.0, "y": 2.0, "z": 0.0},
       "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
     }
   }
   ```

3. **system_status** - 系统状态变化
   ```json
   {
     "type": "system_status",
     "data": {
       "state": 3,
       "state_name": "NAVIGATION"
     }
   }
   ```

4. **nav_feedback** - 导航反馈
   ```json
   {
     "type": "nav_feedback",
     "data": {
       "arrive": 2,
       "finish": 1,
       "all": 5
     }
   }
   ```

### WebSocket 操作

#### 订阅主题

```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  topics: ['qt_notice', 'odometry']
}));
```

#### 取消订阅

```javascript
ws.send(JSON.stringify({
  action: 'unsubscribe',
  topics: ['odometry']
}));
```

#### 心跳

服务器每 30 秒发送一次心跳：
```json
{
  "type": "heartbeat",
  "timestamp": 1634567890.123
}
```

---

## 配置说明

### 环境变量 (.env)

```bash
# ============ 运行模式 ============
SIMULATOR_MODE=true              # 仿真模式开关

# ============ 服务配置 ============
HOST=0.0.0.0                     # 监听地址
PORT=8000                        # 监听端口

# ============ 日志配置 ============
LOG_LEVEL=INFO                   # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/backend.log        # 日志文件路径

# ============ 数据存储 ============
MAP_REGISTRY_FILE=data/map_registry.json   # 地图注册表文件

# ============ CORS 配置 ============
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ============ 真实模式配置 ============
NETWORK_INTERFACE=eth0           # DDS 网络接口
COMMAND_TIMEOUT=5                # 命令超时时间（秒）

# ============ WebSocket 配置 ============
WS_HEARTBEAT_INTERVAL=30         # 心跳间隔（秒）
```

### 配置优先级

1. 环境变量（最高优先级）
2. .env 文件
3. config.py 中的默认值（最低优先级）

---

## 常见问题

### Q1: 如何切换仿真模式和真实模式？

**A**: 修改 `.env` 文件中的 `SIMULATOR_MODE` 变量：

```bash
# 仿真模式
SIMULATOR_MODE=true

# 真实模式
SIMULATOR_MODE=false
```

或在启动时设置环境变量：

```bash
SIMULATOR_MODE=true python main.py
```

### Q2: 真实模式连接不上硬件？

**A**: 检查以下几点：

1. 确认网络接口配置正确：
   ```bash
   # 查看网络接口
   ifconfig
   # 或
   ip addr show
   ```

2. 确认 DDS 网络连通：
   ```bash
   ping <机器人IP>
   ```

3. 检查防火墙设置

4. 查看日志：
   ```bash
   tail -f logs/backend.log
   ```

### Q3: API 返回 500 错误？

**A**: 检查日志文件查看详细错误信息：

```bash
tail -f logs/backend.log
```

常见原因：
- SLAM 服务未正确初始化
- 命令超时
- 参数错误

### Q4: WebSocket 连接断开？

**A**: WebSocket 会自动重连。如果持续断开，检查：

1. 网络连接
2. 服务器日志
3. 客户端是否正确响应心跳

### Q5: 如何查看所有可用命令？

**A**:

```bash
make help
```

或访问 API 文档：http://localhost:8000/docs

---

## 故障排查

### 1. 服务无法启动

**症状**: `python main.py` 执行失败

**解决方案**:

```bash
# 1. 检查 Python 版本
python --version  # 应该是 3.10+

# 2. 重新安装依赖
bash setup.sh

# 3. 检查配置文件
cat .env

# 4. 查看详细错误
python main.py 2>&1 | tee error.log
```

### 2. 命令执行超时

**症状**: API 返回超时错误

**解决方案**:

```bash
# 1. 增加超时时间
# 编辑 .env
COMMAND_TIMEOUT=10

# 2. 检查 SLAM 系统状态
curl http://localhost:8000/api/status/system

# 3. 查看命令统计
curl http://localhost:8000/api/status/commands
```

### 3. 内存占用过高

**症状**: 服务运行一段时间后内存占用过高

**解决方案**:

```bash
# 1. 清理旧命令记录
# 在代码中调用
slam_service.clear_old_commands(max_age=300)

# 2. 重启服务
# Ctrl+C 停止，然后重新启动
```

### 4. 日志文件过大

**解决方案**:

```bash
# 1. 配置日志轮转
# 编辑 logger.py，添加 RotatingFileHandler

# 2. 手动清理
rm logs/backend.log
# 服务会自动创建新文件
```

---

## 更多资源

- **API 文档**: http://localhost:8000/docs
- **开发者文档**: 见 `docs/DEVELOPER.md`
- **项目状态**: 见 `STATUS.md`
- **开发计划**: 见 `DEVELOPMENT_PLAN.md`

---

**版本**: 0.1.0
**最后更新**: 2025-10-17
