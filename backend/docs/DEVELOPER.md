# Unitree B2 SLAM Backend - 开发者文档

## 📋 目录

- [架构概览](#架构概览)
- [核心模块详解](#核心模块详解)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [扩展指南](#扩展指南)
- [性能优化](#性能优化)
- [调试技巧](#调试技巧)

---

## 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│                   (WebSocket + REST API)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  REST API    │  │  WebSocket   │  │   Exceptions │      │
│  │  (17 routes) │  │  (4 topics)  │  │   Handler    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SlamService  │  │ MapManager   │  │CommandExecutor│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│               Communication Layer (Abstraction)              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Publisher   │  │  Subscriber  │                        │
│  └──────┬───────┘  └───────┬──────┘                        │
│         │                  │                                │
│    ┌────▼──────┐    ┌──────▼─────┐                        │
│    │ Real Mode │    │  Sim Mode  │                        │
│    └────┬──────┘    └──────┬─────┘                        │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          │                  │
┌─────────▼──────┐  ┌────────▼──────────┐
│  Unitree SDK   │  │   Simulator       │
│  (DDS/CycloneDD│  │  - Odometry       │
│   S)            │  │  - Notice         │
└─────────────────┘  └───────────────────┘
```

### 模块依赖关系

```
main.py
  ├── config.py (全局配置)
  ├── logger.py (日志系统)
  ├── api/
  │   ├── models.py (数据模型)
  │   ├── dependencies.py (依赖注入)
  │   ├── exceptions.py (异常处理)
  │   ├── mapping.py
  │   ├── relocation.py
  │   ├── navigation.py
  │   ├── topology.py
  │   ├── status.py
  │   ├── websocket.py
  │   └── websocket_manager.py
  └── slam/
      ├── message_types.py (消息定义)
      ├── command_builder.py (命令构建)
      ├── command_executor.py (命令执行)
      ├── slam_service.py (SLAM 服务核心)
      └── map_manager.py (地图管理)
  └── simulator/
      ├── odometry_simulator.py
      ├── notice_simulator.py
      └── simulator_manager.py
```

---

## 核心模块详解

### 1. config.py - 配置管理

**职责**:
- 从环境变量和 .env 文件加载配置
- 提供全局配置对象
- 确保必要的目录存在

**关键配置**:
```python
class Config:
    # 运行模式
    SIMULATOR_MODE: bool = env.bool("SIMULATOR_MODE", default=True)

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # DDS 主题
    TOPIC_QT_COMMAND = "/qt_command"
    TOPIC_QT_NOTICE = "/qt_notice"
    TOPIC_ODOM = "/odom"
    # ... 更多主题
```

**扩展配置**:
```python
# 在 .env 文件中添加
NEW_CONFIG_ITEM=value

# 在 config.py 中添加
NEW_CONFIG_ITEM: str = env.str("NEW_CONFIG_ITEM", default="default_value")
```

---

### 2. slam/slam_service.py - SLAM 服务核心

**职责**:
- 封装 Unitree SLAM 功能
- 管理 Publisher/Subscriber
- 命令执行和状态管理
- 拓扑图管理

**核心类**:

#### SlamService
```python
class SlamService:
    def __init__(self, simulator_mode: bool = None, network_interface: str = None):
        # 初始化发布器/订阅器
        # 注册回调
        # 启动仿真器（如果在仿真模式）

    # 建图
    async def start_mapping(self) -> CommandRecord
    async def end_mapping(self, pcdmap_index: int, save: bool) -> CommandRecord

    # 重定位
    async def start_relocation(self) -> CommandRecord
    async def init_pose(self, x, y, z, qx, qy, qz, qw) -> CommandRecord

    # 导航
    async def start_navigation(self) -> CommandRecord
    async def single_point_nav(self, target_node: int) -> CommandRecord
    async def loop_navigation(self, node_sequence: List[int]) -> CommandRecord

    # 拓扑图
    def add_node_from_odom(self) -> Optional[NodeAttribute]
    async def save_topology(self) -> tuple[CommandRecord, CommandRecord]
```

**Publisher/Subscriber 抽象层**:
```python
class Publisher:
    def init(self): ...
    def write(self, msg): ...

class RealPublisher(Publisher):
    # 使用 Unitree SDK

class SimPublisher(Publisher):
    # 使用仿真器
```

**添加新命令**:

1. 在 `message_types.py` 中定义命令类型
2. 在 `command_builder.py` 中添加构建方法
3. 在 `slam_service.py` 中添加服务方法
4. 在相应的 API router 中添加路由

---

### 3. slam/command_executor.py - 命令执行器

**职责**:
- 管理命令索引分配
- 追踪命令状态
- 超时检查
- 异步等待命令完成

**命令生命周期**:
```
1. [PENDING]  → 命令注册
2. [SENT]     → 命令发送
3. [SUCCESS]  → 收到成功反馈
   [FAILED]   → 收到失败反馈
   [TIMEOUT]  → 超时
```

**使用示例**:
```python
# 1. 获取索引
index = executor.get_next_index()

# 2. 注册命令
executor.register_command(index, "START_MAPPING")

# 3. 发送命令
publisher.write(command)

# 4. 等待完成
record = await executor.wait_for_command(index, timeout=10)

# 5. 检查结果
if record.status == CommandStatus.SUCCESS:
    print(f"命令成功: {record.notice}")
else:
    print(f"命令失败: {record.error}")
```

---

### 4. simulator/ - 仿真模块

**职责**:
- 模拟 SLAM 系统行为
- 生成测试数据
- 支持无硬件开发

**OdometrySimulator**:
```python
class OdometrySimulator:
    def __init__(self, publish_rate=10.0, noise_level=0.01):
        # 里程计发布频率和噪声级别

    async def start(self):
        # 启动发布循环

    def set_velocity(self, vx, vy, omega):
        # 设置机器人速度

    def move_to_point(self, target_x, target_y, speed=0.5):
        # 移动到目标点
```

**NoticeSimulator**:
```python
class NoticeSimulator:
    async def handle_command(self, cmd: QtCommand_):
        # 处理命令，生成模拟响应

    async def handle_save_nodes(self, qt_node: QtNode_):
        # 处理保存节点

    async def _simulate_navigation(self, node_sequence: list):
        # 模拟导航过程
```

**扩展仿真器**:
```python
# 添加新的模拟行为
class NoticeSimulator:
    async def _handle_new_command(self, index: int, cmd: QtCommand_):
        # 添加模拟逻辑
        await asyncio.sleep(self.response_delay)
        await self._send_notice(index, CommandFeedback.SUCCESS, None, "完成")
```

---

### 5. api/ - API 层

**路由结构**:
```python
# mapping.py
@router.post("/api/mapping/start")
async def start_mapping(slam_service: SlamServiceDep):
    record = await slam_service.start_mapping()
    return ApiResponse(
        success=record.status == CommandStatus.SUCCESS,
        message="开始建图成功" if record.status == CommandStatus.SUCCESS else "开始建图失败",
        data={...}
    )
```

**依赖注入**:
```python
# dependencies.py
def get_slam_service_dependency() -> SlamService:
    try:
        return get_slam_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail="SLAM 服务初始化失败")

SlamServiceDep = Annotated[SlamService, Depends(get_slam_service_dependency)]

# 使用
@router.post("/api/example")
async def example(slam_service: SlamServiceDep):
    # slam_service 自动注入
    ...
```

**异常处理**:
```python
# exceptions.py
class ApiException(Exception):
    """API 异常基类"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

# 使用
raise ApiException(status_code=400, message="参数错误")
```

---

### 6. api/websocket_manager.py - WebSocket 管理

**职责**:
- 管理 WebSocket 连接
- 主题订阅管理
- 消息广播
- 心跳保持连接

**核心类**:
```python
class ConnectionManager:
    async def connect(self, websocket: WebSocket, client_id: str):
        # 接受连接

    async def subscribe(self, client_id: str, topic: str):
        # 订阅主题

    async def broadcast(self, message: dict, topic: str = None):
        # 广播消息

    async def send_heartbeat(self):
        # 发送心跳
```

**添加新主题**:
```python
# 1. 在 websocket.py 中定义主题
TOPIC_NEW_DATA = "new_data"

# 2. 注册回调
def on_new_data(data):
    message = {"type": "new_data", "data": {...}}
    asyncio.create_task(manager.broadcast(message, TOPIC_NEW_DATA))

# 3. 在 SLAM 服务中触发
slam_service.register_new_data_callback(on_new_data)
```

---

## 开发环境设置

### 1. 安装开发工具

```bash
# 安装 uv (Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd unitree-b2-slam-web/backend

# 安装依赖
bash setup.sh
source .venv/bin/activate
```

### 2. IDE 配置

#### VS Code
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

#### PyCharm
1. 设置 Python 解释器: `.venv/bin/python`
2. 启用 `ruff` 和 `black` 集成
3. 设置代码风格为 Black

### 3. 环境变量

```bash
# 开发环境
cp .env.example .env.dev

# 编辑配置
SIMULATOR_MODE=true
LOG_LEVEL=DEBUG
```

---

## 代码规范

### 1. Python 代码风格

遵循 PEP 8 和 Black 格式化标准：

```python
# 好的示例
class SlamService:
    """SLAM 服务核心类"""

    def __init__(self, simulator_mode: bool = None):
        """
        初始化 SLAM 服务

        Args:
            simulator_mode: 是否使用仿真模式
        """
        self.simulator_mode = simulator_mode

    async def start_mapping(self) -> CommandRecord:
        """
        开始建图

        Returns:
            命令执行记录
        """
        logger.info("开始建图")
        # ... 实现
```

### 2. 类型注解

强制使用类型注解：

```python
from typing import List, Optional, Dict, Tuple

def process_nodes(
    nodes: List[NodeAttribute],
    filter_func: Optional[Callable[[NodeAttribute], bool]] = None
) -> Tuple[int, Dict[int, NodeAttribute]]:
    """处理节点列表"""
    ...
```

### 3. 文档字符串

使用 Google 风格的文档字符串：

```python
def create_command(
    command_type: CommandType,
    params: Dict[str, Any]
) -> QtCommand_:
    """
    创建命令对象

    Args:
        command_type: 命令类型
        params: 命令参数字典

    Returns:
        QtCommand_ 对象

    Raises:
        ValueError: 如果参数无效
    """
    ...
```

### 4. 错误处理

```python
# 好的示例
try:
    result = await slam_service.start_mapping()
    if result.status != CommandStatus.SUCCESS:
        logger.error(f"建图失败: {result.error}")
        raise ApiException(500, f"建图失败: {result.error}")
except asyncio.TimeoutError:
    logger.error("建图命令超时")
    raise ApiException(504, "建图命令超时")
except Exception as e:
    logger.error(f"建图异常: {e}", exc_info=True)
    raise ApiException(500, "建图失败")
```

---

## 测试指南

### 1. 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
pytest tests/test_simulator_integration.py -v

# 带覆盖率
pytest tests/ --cov=. --cov-report=html
```

### 2. 编写单元测试

```python
# tests/test_command_builder.py
import pytest
from slam.command_builder import CommandBuilder

class TestCommandBuilder:
    @pytest.fixture
    def builder(self):
        return CommandBuilder(lambda: 1)

    def test_build_start_mapping(self, builder):
        index, cmd = builder.build_start_mapping()
        assert index == 1
        assert cmd.command_ == CommandType.START_MAPPING
```

### 3. 编写集成测试

```python
# tests/test_slam_workflow.py
@pytest.mark.asyncio
async def test_complete_mapping_workflow():
    # 初始化服务
    service = SlamService(simulator_mode=True)

    # 开始建图
    record = await service.start_mapping()
    assert record.status == CommandStatus.SUCCESS

    # 添加节点
    node = service.add_node_from_odom()
    assert node is not None

    # 保存拓扑图
    record_n, record_e = await service.save_topology()
    assert record_n.status == CommandStatus.SUCCESS

    # 结束建图
    record = await service.end_mapping(1, True)
    assert record.status == CommandStatus.SUCCESS
```

### 4. 模拟测试

```python
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch('slam.slam_service.get_simulator_manager') as mock_sim:
        # 配置 mock
        mock_sim.return_value = Mock()

        # 测试
        service = SlamService(simulator_mode=True)
        ...
```

---

## 扩展指南

### 1. 添加新的 API 端点

**步骤**:

1. 在 `api/models.py` 中定义请求/响应模型
2. 创建新的路由文件或在现有文件中添加
3. 在 `main.py` 中注册路由

**示例**:

```python
# api/models.py
class NewFeatureRequest(BaseModel):
    param1: str
    param2: int

class NewFeatureResponse(BaseModel):
    result: str

# api/new_feature.py
from fastapi import APIRouter
from api.models import ApiResponse, NewFeatureRequest, NewFeatureResponse
from api.dependencies import SlamServiceDep

router = APIRouter(prefix="/api/new_feature", tags=["New Feature"])

@router.post("/action", response_model=ApiResponse[NewFeatureResponse])
async def perform_action(
    request: NewFeatureRequest,
    slam_service: SlamServiceDep
):
    # 实现逻辑
    result = await slam_service.do_something(request.param1, request.param2)

    return ApiResponse(
        success=True,
        message="操作成功",
        data=NewFeatureResponse(result=result)
    )

# main.py
from api import new_feature
app.include_router(new_feature.router)
```

### 2. 添加新的 SLAM 命令

**步骤**:

1. 在 `message_types.py` 中定义命令类型
2. 在 `command_builder.py` 中添加构建方法
3. 在 `slam_service.py` 中添加服务方法

**示例**:

```python
# message_types.py
class CommandType(IntEnum):
    # ... 现有命令
    NEW_COMMAND = 99

# command_builder.py
class CommandBuilder:
    def build_new_command(self, param: str) -> tuple[int, QtCommand_]:
        """构建新命令"""
        index = self._get_next_index()
        cmd = QtCommand_()
        cmd.seq_ = String_(data=f"index:{index};")
        cmd.command_ = CommandType.NEW_COMMAND
        cmd.param_ = [param]
        return index, cmd

# slam_service.py
class SlamService:
    async def execute_new_command(self, param: str) -> CommandRecord:
        """执行新命令"""
        index, cmd = self._builder.build_new_command(param)
        self._executor.register_command(index, "NEW_COMMAND")
        self.pub_command.write(cmd)
        return await self._executor.wait_for_command(index)

# simulator/notice_simulator.py (仿真支持)
class NoticeSimulator:
    async def handle_command(self, cmd: QtCommand_):
        # ... 现有处理
        elif cmd.command_ == CommandType.NEW_COMMAND:
            await self._handle_new_command(index, cmd)

    async def _handle_new_command(self, index: int, cmd: QtCommand_):
        """处理新命令"""
        await asyncio.sleep(self.response_delay)
        await self._send_notice(
            index,
            CommandFeedback.SUCCESS,
            None,
            "新命令执行成功"
        )
```

### 3. 添加新的 WebSocket 主题

**步骤**:

1. 在 `websocket.py` 中定义主题常量
2. 创建回调函数
3. 注册到 SLAM 服务

**示例**:

```python
# websocket.py
TOPIC_NEW_DATA = "new_data"

def _register_slam_callbacks(slam_service, manager):
    # ... 现有回调

    def on_new_data(data):
        """新数据回调"""
        message = {
            "type": "new_data",
            "timestamp": time.time(),
            "data": {
                "value": data.value,
                "status": data.status
            }
        }
        asyncio.create_task(manager.broadcast(message, TOPIC_NEW_DATA))

    slam_service.register_new_data_callback(on_new_data)

# slam/slam_service.py
class SlamService:
    def __init__(self):
        # ...
        self._new_data_callbacks: List[Callable] = []

    def register_new_data_callback(self, callback: Callable):
        """注册新数据回调"""
        self._new_data_callbacks.append(callback)

    def _trigger_new_data(self, data):
        """触发新数据回调"""
        for callback in self._new_data_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"新数据回调失败: {e}")
```

---

## 性能优化

### 1. 异步操作

使用 `asyncio` 进行并发操作：

```python
# 并发执行多个命令
async def execute_batch_commands():
    results = await asyncio.gather(
        slam_service.start_mapping(),
        slam_service.start_relocation(),
        slam_service.start_navigation(),
        return_exceptions=True  # 不会因一个失败而全部失败
    )
    return results
```

### 2. 连接池

```python
# 使用连接池管理 WebSocket
class ConnectionManager:
    def __init__(self, max_connections=100):
        self.max_connections = max_connections
        self.connections = {}

    async def connect(self, websocket, client_id):
        if len(self.connections) >= self.max_connections:
            raise HTTPException(status_code=503, detail="连接数已达上限")
        # ...
```

### 3. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_node_info(node_id: int) -> NodeAttribute:
    """缓存节点信息"""
    # 查询数据库或计算
    ...
```

### 4. 数据库优化（如果使用）

```python
# 批量插入
async def save_multiple_nodes(nodes: List[NodeAttribute]):
    # 使用批量插入而不是逐个插入
    await db.execute_many(insert_query, nodes)
```

---

## 调试技巧

### 1. 日志调试

```python
# 增加详细日志
logger.debug(f"处理命令: {cmd}")
logger.info(f"命令执行结果: {record}")
logger.error(f"命令失败: {error}", exc_info=True)

# 查看日志
tail -f logs/backend.log | grep ERROR
```

### 2. 断点调试

```python
# 在代码中添加
import pdb; pdb.set_trace()

# 或使用 iPython
import IPython; IPython.embed()
```

### 3. 性能分析

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 执行代码
await slam_service.start_mapping()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 4. 内存分析

```python
import tracemalloc

tracemalloc.start()

# 执行代码
# ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

---

## 更多资源

- **用户指南**: 见 `docs/USER_GUIDE.md`
- **API 文档**: http://localhost:8000/docs
- **项目状态**: 见 `STATUS.md`
- **开发计划**: 见 `DEVELOPMENT_PLAN.md`
- **测试报告**: 见 `TEST_REPORT.md`

---

**版本**: 0.1.0
**最后更新**: 2025-10-17
