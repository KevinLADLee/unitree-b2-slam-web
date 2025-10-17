# Unitree B2 SLAM Web Backend

基于 FastAPI 的 Unitree B2 SLAM 导航服务后端。

## ✨ 特性

- 🚀 RESTful API（建图、导航、重定位、拓扑图管理）
- 📡 WebSocket 实时推送（状态、位姿、通知）
- 🗺️ 地图名称自动映射管理
- 🤖 完整仿真模式（无需真实硬件）
- ⚡ 使用 uv 管理环境，Python 3.10

## 📋 快速开始

### 1. 环境初始化

```bash
# 一键初始化环境（自动创建 Python 3.10 虚拟环境并安装依赖）
bash setup.sh

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 2. 配置

```bash
# 复制配置文件（setup.sh 已自动完成）
cp .env.example .env

# 编辑配置（可选）
nano .env
```

### 3. 运行服务

```bash
# 运行仿真模式（推荐开发时使用）
make run-sim

# 或运行开发服务器（使用 .env 配置）
make run

# 查看所有可用命令
make help
```

### 4. 访问 API 文档

服务启动后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🛠️ 开发命令

```bash
make help          # 显示所有可用命令
make install       # 安装生产依赖
make dev           # 安装开发依赖
make run-sim       # 运行仿真模式
make run           # 运行开发服务器
make test          # 运行测试
make format        # 格式化代码
make lint          # 代码检查
make clean         # 清理临时文件
```

## 📁 项目结构

```
backend/
├── config.py                  # 配置管理
├── main.py                    # FastAPI 应用入口
├── slam/                      # SLAM 服务层
│   ├── map_manager.py        # 地图名称映射管理
│   ├── slam_service.py       # SLAM 核心服务
│   ├── message_types.py      # 消息类型定义
│   └── command_executor.py   # 命令执行器
├── api/                       # API 路由层
│   ├── models.py             # 请求/响应模型
│   ├── routes/               # API 路由
│   └── websocket.py          # WebSocket 推送
├── simulator/                 # 仿真模块
│   ├── mock_robot.py         # 模拟 SDK
│   └── mock_slam.py          # 模拟 SLAM
└── tests/                     # 测试模块
```

## 🔧 配置说明

主要环境变量（`.env`）：

```bash
# 运行模式
SIMULATOR_MODE=true           # true: 仿真模式, false: 真实模式

# 网络配置（仅真实模式需要）
NETWORK_INTERFACE=            # 网络接口，如 'eth0'

# 服务配置
HOST=0.0.0.0                  # 监听地址
PORT=8000                     # 监听端口

# 日志配置
LOG_LEVEL=INFO                # 日志级别

# 数据存储
MAP_STORAGE_PATH=./data/map_registry.json
```

## 📚 API 使用示例

### 建图

```bash
# 开始建图
curl -X POST http://localhost:8000/api/mapping/start \
  -H "Content-Type: application/json" \
  -d '{"map_name": "warehouse_floor1", "description": "仓库一楼"}'

# 结束建图
curl -X POST http://localhost:8000/api/mapping/end \
  -H "Content-Type: application/json" \
  -d '{"map_name": "warehouse_floor1", "save_map": true}'

# 列出所有地图
curl http://localhost:8000/api/mapping/list
```

### 导航

```bash
# 开启导航
curl -X POST http://localhost:8000/api/navigation/start

# 单点导航
curl -X POST http://localhost:8000/api/navigation/single \
  -H "Content-Type: application/json" \
  -d '{"target_node": 5}'

# 多点循环
curl -X POST http://localhost:8000/api/navigation/loop \
  -H "Content-Type: application/json" \
  -d '{"node_sequence": [1, 2, 3, 4]}'
```

## 🧪 测试

```bash
# 运行所有测试
make test

# 快速测试（不生成覆盖率）
make test-fast
```

## 📖 文档

- [开发计划](./DEVELOPMENT_PLAN.md) - 完整的开发计划和架构设计
- [API 文档](http://localhost:8000/docs) - Swagger UI（需先启动服务）

## 🔄 开发流程

1. 创建功能分支
2. 编写代码
3. 运行测试: `make test`
4. 格式化代码: `make format`
5. 代码检查: `make lint`
6. 提交代码

## 🐛 故障排除

### uv 安装失败

```bash
# 手动安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python 3.10 未安装

```bash
# Ubuntu/Debian
sudo apt install python3.10 python3.10-venv

# macOS
brew install python@3.10
```

### 虚拟环境激活失败

```bash
# 确保使用正确的命令
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows (CMD)
.venv\Scripts\Activate.ps1 # Windows (PowerShell)
```

## 📞 支持

如有问题，请查看：
- [开发计划文档](./DEVELOPMENT_PLAN.md)
- [Issue Tracker](https://github.com/your-repo/issues)

## 📄 许可证

待定

---

**版本**: v0.1.0
**状态**: 开发中
**最后更新**: 2024-01-15
