#!/bin/bash
# ============================================
# Unitree B2 SLAM Backend 环境初始化脚本
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Unitree B2 SLAM Backend 环境初始化${NC}"
echo "======================================"
echo ""

# 1. 检查 uv 是否安装
echo -e "${YELLOW}📦 检查 uv 安装状态...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv 未安装，正在安装...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✅ uv 安装完成${NC}"
else
    echo -e "${GREEN}✅ uv 已安装: $(uv --version)${NC}"
fi
echo ""

# 2. 检查 Python 版本
echo -e "${YELLOW}🐍 检查 Python 3.10 安装状态...${NC}"
if ! command -v python3.10 &> /dev/null; then
    echo -e "${RED}❌ Python 3.10 未安装${NC}"
    echo -e "${YELLOW}请先安装 Python 3.10:${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3.10 python3.10-venv"
    echo "  macOS: brew install python@3.10"
    exit 1
else
    echo -e "${GREEN}✅ Python 3.10 已安装: $(python3.10 --version)${NC}"
fi
echo ""

# 3. 创建虚拟环境
echo -e "${YELLOW}📦 创建 Python 3.10 虚拟环境...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境已存在，跳过创建${NC}"
else
    uv venv --python 3.10
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi
echo ""

# 4. 激活虚拟环境提示
echo -e "${GREEN}⚡ 虚拟环境已就绪！${NC}"
echo -e "${YELLOW}请运行以下命令激活环境：${NC}"
echo ""
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo -e "  ${BLUE}.venv\\Scripts\\activate${NC}     # Windows"
else
    echo -e "  ${BLUE}source .venv/bin/activate${NC}  # Linux/macOS"
fi
echo ""

# 5. 安装依赖
read -p "是否现在安装项目依赖？[Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo -e "${YELLOW}📥 安装生产依赖...${NC}"
    source .venv/bin/activate 2>/dev/null || . .venv/bin/activate
    uv pip install -e .
    echo -e "${GREEN}✅ 生产依赖安装完成${NC}"
    echo ""

    read -p "是否安装开发依赖（测试、格式化工具等）？[Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo -e "${YELLOW}📥 安装开发依赖...${NC}"
        uv pip install -e ".[dev]"
        echo -e "${GREEN}✅ 开发依赖安装完成${NC}"
    fi
fi
echo ""

# 6. 创建必要目录
echo -e "${YELLOW}📁 创建数据和日志目录...${NC}"
mkdir -p data
mkdir -p logs
touch data/.gitkeep
touch logs/.gitkeep
echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 7. 创建 .env 配置文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 创建 .env 配置文件...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env 文件已创建（从 .env.example 复制）${NC}"
    echo -e "${YELLOW}⚠️  请根据需要修改 .env 中的配置${NC}"
else
    echo -e "${YELLOW}⚠️  .env 文件已存在，跳过创建${NC}"
fi
echo ""

# 8. 完成提示
echo ""
echo -e "${GREEN}✅ 环境初始化完成！${NC}"
echo "======================================"
echo ""
echo -e "${BLUE}🎯 快速启动指南：${NC}"
echo ""
echo "  1. 激活虚拟环境:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo -e "     ${BLUE}.venv\\Scripts\\activate${NC}"
else
    echo -e "     ${BLUE}source .venv/bin/activate${NC}"
fi
echo ""
echo "  2. 运行开发服务器（仿真模式）:"
echo -e "     ${BLUE}make run-sim${NC}"
echo ""
echo "  3. 查看所有可用命令:"
echo -e "     ${BLUE}make help${NC}"
echo ""
echo -e "${YELLOW}📚 更多信息请查看 README.md 和 DEVELOPMENT_PLAN.md${NC}"
echo ""
