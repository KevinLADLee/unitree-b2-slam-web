# Unitree B2 SLAM Backend - 部署指南

## 📋 目录

- [部署前准备](#部署前准备)
- [生产环境部署](#生产环境部署)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [监控与维护](#监控与维护)
- [故障排查](#故障排查)
- [安全建议](#安全建议)

---

## 部署前准备

### 1. 系统要求

**硬件要求**:
- CPU: 2 核心以上
- 内存: 4GB 以上
- 磁盘: 10GB+ 可用空间
- 网络: 与 Unitree B2 机器人在同一网络

**软件要求**:
- 操作系统: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python: 3.10 或更高版本
- Unitree SDK2 (真实模式)

### 2. 依赖安装

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# 安装 uv (推荐的包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 3. 网络配置

确保服务器与 Unitree B2 机器人网络连通:

```bash
# 查看网络接口
ip addr show

# 测试与机器人连通性
ping <机器人IP地址>

# 检查 DDS 端口是否开放 (通常是 7400-7500)
sudo netstat -tulpn | grep 74
```

---

## 生产环境部署

生产环境推荐使用进程管理工具（PM2 或 Supervisor）来管理服务，确保服务的稳定运行和自动重启。

### 方法 1: 使用 PM2 部署（推荐）

PM2 是一个功能强大的进程管理器，支持负载均衡、日志管理、自动重启等功能。

#### 1. 安装 PM2

```bash
# 全局安装 PM2
npm install -g pm2

# 或使用 yarn
yarn global add pm2
```

#### 2. 部署项目

```bash
# 创建部署目录
sudo mkdir -p /opt/unitree-slam
sudo chown $USER:$USER /opt/unitree-slam
cd /opt/unitree-slam

# 克隆代码
git clone <repository-url> .
cd backend

# 配置环境
cp .env.production .env
nano .env  # 编辑配置

# 安装依赖
bash setup.sh
```

#### 3. 配置 PM2

项目已包含 PM2 配置文件 `pm2.config.json`，可直接使用：

```json
{
  "name": "unitree-slam-backend",
  "script": "./start.sh",
  "cwd": "/opt/unitree-slam/backend",
  "interpreter": "/bin/bash",
  "instances": 1,
  "exec_mode": "fork",
  "autorestart": true,
  "watch": false,
  "max_memory_restart": "500M"
}
```

**修改配置文件中的路径**：

```bash
# 编辑 pm2.config.json
nano pm2.config.json

# 修改 cwd 为实际路径
"cwd": "/opt/unitree-slam/backend"
```

#### 4. 启动服务

```bash
# 使用 PM2 启动服务
pm2 start pm2.config.json

# 或使用 Makefile
make pm2-start

# 查看状态
pm2 status

# 查看日志
pm2 logs unitree-slam-backend

# 查看详细信息
pm2 show unitree-slam-backend
```

#### 5. 设置开机自启

```bash
# 保存 PM2 进程列表
pm2 save

# 生成启动脚本
pm2 startup

# 按照提示执行生成的命令（通常需要 sudo）
# 例如：
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp /home/$USER
```

#### 6. PM2 常用命令

```bash
# 启动
pm2 start pm2.config.json

# 停止
pm2 stop unitree-slam-backend

# 重启
pm2 restart unitree-slam-backend

# 删除
pm2 delete unitree-slam-backend

# 查看日志
pm2 logs unitree-slam-backend

# 实时监控
pm2 monit

# 清空日志
pm2 flush
```

**Makefile 快捷命令**：

```bash
make pm2-start      # 启动服务
make pm2-stop       # 停止服务
make pm2-restart    # 重启服务
make pm2-logs       # 查看日志
make pm2-status     # 查看状态
make pm2-delete     # 删除进程
```

---

### 方法 2: 使用 Supervisor 部署

Supervisor 是一个 Python 实现的进程管理工具，适合 Linux 服务器环境。

#### 1. 安装 Supervisor

```bash
# Ubuntu/Debian
sudo apt install supervisor -y

# CentOS/RHEL
sudo yum install supervisor -y
```

#### 2. 部署项目

```bash
# 创建部署目录
sudo mkdir -p /opt/unitree-slam
sudo chown $USER:$USER /opt/unitree-slam
cd /opt/unitree-slam

# 克隆代码
git clone <repository-url> .
cd backend

# 配置环境
cp .env.production .env
nano .env

# 安装依赖
bash setup.sh
```

#### 3. 安装 Supervisor 配置

项目已包含 Supervisor 配置文件 `supervisor.conf`：

```bash
# 编辑配置文件，修改用户和路径
nano supervisor.conf

# 修改以下配置：
# user=<your-username>  # 改为实际用户名
# command=/opt/unitree-slam/backend/start.sh  # 确认路径正确
# directory=/opt/unitree-slam/backend

# 使用 Makefile 安装配置
make supervisor-install

# 或手动安装
sudo cp supervisor.conf /etc/supervisor/conf.d/unitree-slam.conf
sudo supervisorctl reread
sudo supervisorctl update
```

#### 4. 启动服务

```bash
# 启动服务
sudo supervisorctl start unitree-slam-backend

# 或使用 Makefile
make supervisor-start

# 查看状态
sudo supervisorctl status unitree-slam-backend

# 查看日志
sudo tail -f /var/log/supervisor/unitree-slam-stdout.log
```

#### 5. Supervisor 常用命令

```bash
# 启动服务
sudo supervisorctl start unitree-slam-backend

# 停止服务
sudo supervisorctl stop unitree-slam-backend

# 重启服务
sudo supervisorctl restart unitree-slam-backend

# 查看所有进程状态
sudo supervisorctl status

# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 查看日志
sudo tail -f /var/log/supervisor/unitree-slam-stdout.log
sudo tail -f /var/log/supervisor/unitree-slam-stderr.log
```

**Makefile 快捷命令**：

```bash
make supervisor-install   # 安装配置
make supervisor-start     # 启动服务
make supervisor-stop      # 停止服务
make supervisor-restart   # 重启服务
make supervisor-status    # 查看状态
make supervisor-logs      # 查看日志
```

---

### 方法 3: systemd 服务（系统级部署）

#### 1. 克隆项目

```bash
# 创建部署目录
sudo mkdir -p /opt/unitree-slam
sudo chown $USER:$USER /opt/unitree-slam
cd /opt/unitree-slam

# 克隆代码
git clone <repository-url> .
cd backend
```

#### 2. 配置环境

```bash
# 复制生产配置
cp .env.production .env

# 编辑配置文件
nano .env
```

**关键配置项**:
```bash
# 运行模式（生产环境使用真实模式）
SIMULATOR_MODE=false

# 网络接口（根据实际网卡名称修改）
NETWORK_INTERFACE=eth0

# 服务配置
HOST=0.0.0.0
PORT=8000

# 日志级别
LOG_LEVEL=INFO

# CORS 配置（前端访问地址）
CORS_ORIGINS=http://localhost:3000,http://<前端服务器IP>:3000

# 命令超时
COMMAND_TIMEOUT=10
```

#### 3. 安装依赖

```bash
# 运行安装脚本
bash setup.sh

# 激活虚拟环境
source .venv/bin/activate

# 验证安装
python -c "import fastapi, uvicorn; print('✅ 依赖安装成功')"
```

#### 4. 创建 systemd 服务

创建服务文件 `/etc/systemd/system/unitree-slam.service`:

```ini
[Unit]
Description=Unitree B2 SLAM Backend Service
After=network.target

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/opt/unitree-slam/backend
Environment="PATH=/opt/unitree-slam/backend/.venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/unitree-slam/backend/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/unitree-slam/stdout.log
StandardError=append:/var/log/unitree-slam/stderr.log

[Install]
WantedBy=multi-user.target
```

**创建日志目录**:
```bash
sudo mkdir -p /var/log/unitree-slam
sudo chown $USER:$USER /var/log/unitree-slam
```

#### 5. 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start unitree-slam

# 查看状态
sudo systemctl status unitree-slam

# 设置开机自启
sudo systemctl enable unitree-slam

# 查看日志
sudo journalctl -u unitree-slam -f
```

---

### 方法 2: 使用反向代理（推荐用于生产环境）

生产环境建议使用 Nginx 作为反向代理，提供 HTTPS 支持。

#### 1. 安装 Nginx

```bash
sudo apt install nginx -y
```

#### 2. 配置 Nginx

创建配置文件 `/etc/nginx/sites-available/unitree-slam`:

```nginx
upstream unitree_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name <your-domain-or-ip>;

    # 日志配置
    access_log /var/log/nginx/unitree-slam-access.log;
    error_log /var/log/nginx/unitree-slam-error.log;

    # API 请求
    location /api {
        proxy_pass http://unitree_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://unitree_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # WebSocket 超时配置
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # API 文档
    location /docs {
        proxy_pass http://unitree_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://unitree_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://unitree_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/unitree-slam /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

#### 4. 配置 HTTPS (可选，推荐)

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取 SSL 证书
sudo certbot --nginx -d <your-domain>

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 配置说明

### 环境变量配置

所有配置通过 `.env` 文件管理，生产环境配置示例见 `.env.production`。

**核心配置项**:

| 配置项 | 说明 | 默认值 | 生产建议 |
|--------|------|--------|----------|
| `SIMULATOR_MODE` | 仿真模式开关 | `true` | `false` |
| `NETWORK_INTERFACE` | DDS 网络接口 | `None` | `eth0` (根据实际) |
| `LOG_LEVEL` | 日志级别 | `INFO` | `INFO` 或 `WARNING` |
| `LOG_MAX_BYTES` | 日志文件大小上限 | `10485760` (10MB) | `10485760` |
| `LOG_BACKUP_COUNT` | 日志备份数量 | `5` | `5-10` |
| `COMMAND_TIMEOUT` | 命令超时（秒） | `5` | `10` |
| `WS_HEARTBEAT_INTERVAL` | WebSocket 心跳间隔 | `30` | `30` |
| `CORS_ORIGINS` | 允许的跨域源 | 本地地址 | 实际前端地址 |

### 日志配置

日志系统支持自动轮转，防止日志文件过大：

```bash
# 配置日志轮转参数
LOG_MAX_BYTES=10485760        # 单个文件最大 10MB
LOG_BACKUP_COUNT=5            # 保留 5 个备份文件
```

日志文件位置:
- 应用日志: `logs/backend.log`
- 系统日志: `/var/log/unitree-slam/` (如使用 systemd)

### 性能调优

**1. 命令超时时间**:
```bash
# 根据网络延迟和机器人响应速度调整
COMMAND_TIMEOUT=10  # 10 秒
```

**2. WebSocket 连接数**:
```bash
# 限制最大 WebSocket 连接数
WS_MAX_CONNECTIONS=100
```

**3. 里程计发布频率**:
```bash
# 真实模式下由硬件控制，仅仿真模式有效
ODOM_PUBLISH_RATE=10  # 10Hz
```

---

## 服务管理

### systemd 命令

```bash
# 启动服务
sudo systemctl start unitree-slam

# 停止服务
sudo systemctl stop unitree-slam

# 重启服务
sudo systemctl restart unitree-slam

# 查看状态
sudo systemctl status unitree-slam

# 查看日志
sudo journalctl -u unitree-slam -f

# 查看最近 100 行日志
sudo journalctl -u unitree-slam -n 100

# 启用开机自启
sudo systemctl enable unitree-slam

# 禁用开机自启
sudo systemctl disable unitree-slam
```

### 直接运行（调试用）

```bash
cd /opt/unitree-slam/backend
source .venv/bin/activate
python main.py
```

---

## 监控与维护

### 1. 健康检查

创建健康检查脚本 `check_health.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000/api/status/system"

# 检查 API 是否响应
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $response -eq 200 ]; then
    echo "✅ 服务运行正常"
    exit 0
else
    echo "❌ 服务异常: HTTP $response"
    exit 1
fi
```

设置定时任务:

```bash
# 编辑 crontab
crontab -e

# 每 5 分钟检查一次
*/5 * * * * /opt/unitree-slam/backend/check_health.sh >> /var/log/unitree-slam/health.log 2>&1
```

### 2. 日志监控

```bash
# 查看错误日志
tail -f logs/backend.log | grep ERROR

# 查看警告日志
tail -f logs/backend.log | grep WARNING

# 统计错误数量
grep ERROR logs/backend.log | wc -l
```

### 3. 性能监控

创建性能监控脚本 `monitor.sh`:

```bash
#!/bin/bash

# 获取进程 PID
PID=$(pgrep -f "python main.py")

if [ -z "$PID" ]; then
    echo "服务未运行"
    exit 1
fi

# CPU 和内存占用
echo "=== 性能监控 ==="
echo "PID: $PID"
ps -p $PID -o %cpu,%mem,cmd

# 网络连接数
echo "=== 网络连接 ==="
netstat -an | grep :8000 | wc -l
```

### 4. 备份策略

**数据备份**:

```bash
# 创建备份脚本 backup.sh
#!/bin/bash

BACKUP_DIR="/backup/unitree-slam"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据目录
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/unitree-slam/backend/data

# 备份配置
cp /opt/unitree-slam/backend/.env $BACKUP_DIR/env_$DATE

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR"
```

设置每日备份:

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /opt/unitree-slam/backend/backup.sh >> /var/log/unitree-slam/backup.log 2>&1
```

### 5. 日志清理

```bash
# 创建日志清理脚本 cleanup_logs.sh
#!/bin/bash

LOG_DIR="/opt/unitree-slam/backend/logs"

# 删除 30 天前的日志备份
find $LOG_DIR -name "*.log.*" -mtime +30 -delete

echo "日志清理完成"
```

---

## 故障排查

### 1. 服务无法启动

**症状**: `systemctl start unitree-slam` 失败

**排查步骤**:

```bash
# 1. 查看详细错误
sudo journalctl -u unitree-slam -n 50

# 2. 检查配置文件
cat /opt/unitree-slam/backend/.env

# 3. 检查 Python 环境
/opt/unitree-slam/backend/.venv/bin/python --version

# 4. 手动运行测试
cd /opt/unitree-slam/backend
source .venv/bin/activate
python main.py
```

### 2. 无法连接硬件

**症状**: 真实模式下提示 "DDS 初始化失败"

**排查步骤**:

```bash
# 1. 检查网络连通性
ping <机器人IP>

# 2. 检查网络接口配置
ip addr show

# 3. 检查 DDS 端口
sudo netstat -tulpn | grep 74

# 4. 验证 Unitree SDK
python -c "from unitree_sdk2py.core.channel import ChannelFactoryInitialize; print('✅ SDK 正常')"
```

### 3. API 响应慢

**症状**: API 请求超时或响应时间过长

**排查步骤**:

```bash
# 1. 检查系统资源
top
free -h
df -h

# 2. 检查命令超时配置
grep COMMAND_TIMEOUT /opt/unitree-slam/backend/.env

# 3. 查看命令统计
curl http://localhost:8000/api/status/commands

# 4. 调整超时时间
# 编辑 .env
COMMAND_TIMEOUT=15  # 增加到 15 秒
```

### 4. WebSocket 频繁断开

**症状**: 前端 WebSocket 连接不稳定

**排查步骤**:

```bash
# 1. 检查心跳配置
grep WS_HEARTBEAT_INTERVAL /opt/unitree-slam/backend/.env

# 2. 检查 Nginx 配置（如使用）
sudo nginx -t

# 3. 查看 WebSocket 连接日志
tail -f logs/backend.log | grep WebSocket

# 4. 调整心跳间隔
WS_HEARTBEAT_INTERVAL=15  # 减少到 15 秒
```

### 5. 日志文件过大

**症状**: 磁盘空间不足

**解决方案**:

```bash
# 1. 检查日志文件大小
du -sh /opt/unitree-slam/backend/logs/*

# 2. 手动清理
rm /opt/unitree-slam/backend/logs/*.log.*

# 3. 调整日志轮转配置
# 编辑 .env
LOG_MAX_BYTES=5242880      # 减少到 5MB
LOG_BACKUP_COUNT=3         # 只保留 3 个备份

# 4. 降低日志级别
LOG_LEVEL=WARNING
```

---

## 安全建议

### 1. 网络安全

```bash
# 配置防火墙，只允许必要的端口
sudo ufw allow 8000/tcp
sudo ufw allow from <前端服务器IP> to any port 8000
sudo ufw enable
```

### 2. 访问控制

**限制 CORS 源**:

```bash
# .env 中配置
CORS_ORIGINS=http://your-frontend-domain.com
```

**禁用生产环境的 API 文档** (可选):

```bash
# .env 中配置
ENABLE_DOCS=false
```

### 3. 日志安全

```bash
# 设置日志文件权限
chmod 600 /opt/unitree-slam/backend/logs/*.log
chown $USER:$USER /opt/unitree-slam/backend/logs/*.log
```

### 4. 更新维护

```bash
# 定期更新依赖
cd /opt/unitree-slam/backend
source .venv/bin/activate
uv sync

# 检查安全漏洞
pip-audit
```

---

## 更新部署

### 代码更新

```bash
# 停止服务
sudo systemctl stop unitree-slam

# 备份当前版本
cp -r /opt/unitree-slam/backend /opt/unitree-slam/backend.backup

# 拉取最新代码
cd /opt/unitree-slam
git pull origin main

# 更新依赖
cd backend
source .venv/bin/activate
uv sync

# 重启服务
sudo systemctl start unitree-slam

# 验证
sudo systemctl status unitree-slam
curl http://localhost:8000/api/status/system
```

### 配置更新

```bash
# 备份当前配置
cp /opt/unitree-slam/backend/.env /opt/unitree-slam/backend/.env.backup

# 对比新旧配置模板
diff .env.production .env

# 手动合并新配置
nano .env

# 重启服务
sudo systemctl restart unitree-slam
```

---

## 回滚操作

```bash
# 停止服务
sudo systemctl stop unitree-slam

# 恢复备份
rm -rf /opt/unitree-slam/backend
mv /opt/unitree-slam/backend.backup /opt/unitree-slam/backend

# 重启服务
sudo systemctl start unitree-slam
```

---

## 附录

### A. 完整部署检查清单

- [ ] 系统要求满足
- [ ] Python 3.10+ 已安装
- [ ] 依赖已安装完成
- [ ] 配置文件已正确设置
- [ ] 网络接口已配置
- [ ] 与机器人网络连通
- [ ] systemd 服务已创建
- [ ] 服务可正常启动
- [ ] API 可正常访问
- [ ] WebSocket 连接正常
- [ ] 日志轮转已配置
- [ ] 备份脚本已设置
- [ ] 监控已配置
- [ ] 防火墙已配置
- [ ] HTTPS 已配置（可选）

### B. 常用端口

| 端口 | 用途 | 协议 |
|------|------|------|
| 8000 | FastAPI HTTP | TCP |
| 8000 | WebSocket | TCP |
| 80 | Nginx HTTP | TCP |
| 443 | Nginx HTTPS | TCP |
| 7400-7500 | DDS 通信 | UDP/TCP |

### C. 参考文档

- **用户指南**: `docs/USER_GUIDE.md`
- **开发者文档**: `docs/DEVELOPER.md`
- **API 文档**: http://localhost:8000/docs
- **项目状态**: `STATUS.md`

---

**版本**: 1.0.0
**最后更新**: 2025-10-17
**维护者**: Unitree SLAM Team
