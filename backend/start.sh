#!/bin/bash
#
# Unitree B2 SLAM Backend 启动脚本
# 适用于 PM2 / Supervisor 等进程管理工具
#

# ==================== 配置区域 ====================

# 项目根目录（自动检测脚本所在目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Python 虚拟环境路径
VENV_DIR="$PROJECT_DIR/.venv"

# Python 可执行文件
PYTHON_BIN="$VENV_DIR/bin/python"

# 主程序文件
MAIN_FILE="$PROJECT_DIR/main.py"

# 环境变量文件
ENV_FILE="$PROJECT_DIR/.env"

# ==================== 环境检查 ====================

echo "🚀 Unitree B2 SLAM Backend 启动中..."
echo "================================================"
echo "项目目录: $PROJECT_DIR"
echo "Python: $PYTHON_BIN"
echo "主程序: $MAIN_FILE"
echo "================================================"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 错误: 虚拟环境不存在: $VENV_DIR"
    echo "请运行 'bash setup.sh' 安装依赖"
    exit 1
fi

# 检查 Python
if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ 错误: Python 可执行文件不存在: $PYTHON_BIN"
    exit 1
fi

# 检查主程序
if [ ! -f "$MAIN_FILE" ]; then
    echo "❌ 错误: 主程序文件不存在: $MAIN_FILE"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  警告: .env 文件不存在，将使用默认配置"
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo "提示: 可以从 .env.example 复制配置文件"
    fi
fi

# ==================== 创建必要目录 ====================

mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"

# ==================== 加载环境变量 ====================

if [ -f "$ENV_FILE" ]; then
    echo "✅ 加载环境变量: $ENV_FILE"
    # 导出环境变量（跳过注释和空行）
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# ==================== 启动服务 ====================

echo "================================================"
echo "🎯 启动模式: ${SIMULATOR_MODE:-true}"
echo "📡 网络接口: ${NETWORK_INTERFACE:-默认}"
echo "🌐 监听地址: ${HOST:-0.0.0.0}:${PORT:-8000}"
echo "📝 日志级别: ${LOG_LEVEL:-INFO}"
echo "================================================"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 启动 Python 应用
exec "$PYTHON_BIN" "$MAIN_FILE"
