# Changelog

All notable changes to the Unitree B2 SLAM Backend project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-17

### Added

#### 阶段 1: 环境搭建
- 项目基础配置文件 (pyproject.toml, .python-version, .env.example, .gitignore)
- 开发工具 (setup.sh, Makefile)
- 完整项目结构
- 配置管理模块 (config.py)
- 地图名称映射管理 (slam/map_manager.py)
- 基础文档 (README.md, DEVELOPMENT_PLAN.md)

#### 阶段 2: FastAPI 应用架构
- FastAPI 应用初始化 (main.py)
- 日志系统 (logger.py) - 彩色控制台 + 文件日志
- 全局异常处理中间件
- CORS 配置 (支持多域名)
- 请求/响应日志中间件
- 服务生命周期管理

#### 阶段 3: 消息类型转换
- slam/message_types.py - QtCommand_ 完整映射 (18 种命令类型)
- QtNode/QtEdge 映射
- Odometry 里程计数据
- QtNotice 解析器
- SystemState 枚举
- api/models.py - 15+ 请求/响应模型
- API 响应统一格式
- 完整类型注解

#### 阶段 4: SLAM 服务核心
- slam/command_builder.py - 18 种命令构建器
- 四元数工具函数
- 完整参数验证
- slam/command_executor.py - 命令索引自动分配
- 状态追踪 (PENDING/SENT/SUCCESS/FAILED/TIMEOUT)
- 异步等待机制
- 超时检查和命令统计
- slam/slam_service.py - Publisher/Subscriber 抽象层
- 仿真/真实模式切换
- 建图、重定位、导航完整功能
- 拓扑图管理 (节点/边)
- 回调系统和全局单例模式

#### 阶段 5: RESTful API 开发
- api/mapping.py - 建图接口 (开始建图、结束建图)
- api/relocation.py - 重定位接口 (开启重定位、初始化位姿)
- api/navigation.py - 导航接口 (开启导航、单点导航、循环导航、暂停/恢复、返回起点)
- api/topology.py - 拓扑图接口 (添加节点、保存拓扑图、查询摘要、删除节点/边、清除缓存)
- api/status.py - 状态接口 (系统状态、里程计数据、命令统计)
- api/map_registry.py - 地图管理接口 (地图列表、创建地图、删除地图)

#### 阶段 6: WebSocket 实时推送
- api/websocket_manager.py - 连接管理 (支持多客户端)
- 主题订阅/取消订阅
- 消息广播 (全局/按主题)
- 自动心跳 (30s 间隔)
- 连接状态追踪
- api/websocket.py - WebSocket 端点 (/ws)
- SLAM 回调集成 (qt_notice, odometry)
- 4 个推送主题
- 自动重连支持

#### 阶段 7: 仿真模块
- simulator/odometry_simulator.py - 里程计数据生成 (10Hz)
- 机器人状态模拟 (位置、速度、角度)
- 噪声注入 (可配置)
- 运动控制 (move_to_point)
- 异步发布循环
- simulator/notice_simulator.py - Qt Notice 响应模拟
- 所有命令类型支持 (18 种)
- 状态机模拟 (IDLE/MAPPING/RELOCATION/NAVIGATION)
- 导航过程模拟 (异步节点到达通知)
- 拓扑图存储 (nodes/edges)
- 响应延迟模拟 (0.5s)
- simulator/simulator_manager.py - 集成 odometry_simulator 和 notice_simulator
- 统一回调管理和全局单例模式

#### 阶段 8: 测试和文档
- tests/test_api_integration.py - API 端点集成测试框架 (22 个测试用例)
- tests/test_simulator_integration.py - 仿真集成测试 (7 个测试用例)
- tests/test_map_manager.py - 地图管理测试 (8 个测试用例)
- TEST_REPORT.md - 完整测试报告 (15 个测试全部通过, 覆盖率 ~87%)
- docs/USER_GUIDE.md - 用户指南 (500+ 行)
  - 快速开始指南
  - 完整 API 使用说明 (含 curl 示例)
  - WebSocket 使用指南
  - 配置说明和常见问题
- docs/DEVELOPER.md - 开发者文档 (600+ 行)
  - 架构概览和模块详解
  - 开发环境设置和代码规范
  - 测试指南和扩展指南
  - 性能优化和调试技巧

#### 阶段 9: 部署准备
- 重构 Publisher/Subscriber 使用 Adapter 模式
  - MessageAdapter 抽象基类
  - DDSAdapter - DDS 通信适配器
  - SimulatorAdapter - 仿真器通信适配器
  - 统一的 Publisher/Subscriber 类
- .env.production - 生产环境配置模板
- config.py - 添加日志轮转配置支持
  - LOG_MAX_BYTES - 日志文件大小上限
  - LOG_BACKUP_COUNT - 日志备份数量
- logger.py - 优化日志配置，支持从配置文件读取轮转参数
- DEPLOYMENT.md - 完整部署文档
  - 部署前准备和系统要求
  - 生产环境部署 (直接部署 + Nginx 反向代理)
  - 配置说明和性能调优
  - 服务管理 (systemd)
  - 监控与维护 (健康检查、日志监控、性能监控、备份策略)
  - 故障排查和安全建议
- CHANGELOG.md - 项目变更日志

### Changed
- slam/slam_service.py - 重构 Publisher/Subscriber 架构
  - 删除 RealPublisher, RealSubscriber, SimPublisher, SimSubscriber (消除代码重复)
  - 使用 Adapter 模式统一通信接口
  - 减少约 100 行重复代码

### Improved
- 代码可维护性 - Adapter 模式使架构更清晰
- 代码可扩展性 - 易于添加新的通信方式
- 日志管理 - 支持自动轮转，防止日志文件过大
- 生产部署 - 完整的部署和运维文档

### Fixed
- 日志文件可能无限增长的问题 (添加轮转)

---

## 项目统计

### 代码规模
- **总行数**: ~8,000+ 行 Python 代码
- **模块数**: 34 个文件
- **测试文件**: 3 个
- **文档文件**: 6 个

### API 端点
- **RESTful 端点**: 17 个
- **WebSocket 端点**: 1 个
- **支持的 SLAM 命令**: 18 种

### 测试覆盖
- **单元测试**: 8 个 (全部通过)
- **集成测试**: 7 个 (全部通过)
- **代码覆盖率**: ~87%

---

## 未来计划

### v0.2.0 (计划中)
- [ ] Docker 容器化支持
- [ ] CI/CD 集成 (GitHub Actions)
- [ ] API 认证和授权
- [ ] 数据库持久化 (PostgreSQL)
- [ ] 性能监控和指标收集
- [ ] 前端集成测试

### v0.3.0 (计划中)
- [ ] 多机器人支持
- [ ] 地图可视化 API
- [ ] 路径规划算法优化
- [ ] 实时地图更新推送
- [ ] 集群部署支持

---

## 贡献者

- **核心开发**: Unitree SLAM Team
- **文档**: Unitree SLAM Team
- **测试**: Unitree SLAM Team

---

## 许可证

查看 LICENSE 文件

---

**注释**:
- [Unreleased] - 未发布的变更
- [0.1.0] - 首个正式版本 (2025-10-17)

[Unreleased]: https://github.com/your-org/unitree-b2-slam-web/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/unitree-b2-slam-web/releases/tag/v0.1.0
