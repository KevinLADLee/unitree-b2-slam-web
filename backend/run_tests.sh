#!/bin/bash
# 快速测试脚本

set -e

echo "🧪 Unitree B2 SLAM Backend 测试套件"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试计数
PASSED=0
FAILED=0

run_test() {
    TEST_NAME="$1"
    TEST_CMD="$2"

    echo -e "${YELLOW}运行测试: ${TEST_NAME}${NC}"

    if eval "$TEST_CMD"; then
        echo -e "${GREEN}✅ ${TEST_NAME} 通过${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ ${TEST_NAME} 失败${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# 确保在 backend 目录
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ 请在 backend 目录下运行此脚本${NC}"
    exit 1
fi

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  未检测到虚拟环境，尝试激活...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}❌ 虚拟环境不存在，请先运行 bash setup.sh${NC}"
        exit 1
    fi
fi

echo "✅ 虚拟环境已激活"
echo ""

# 运行测试
run_test "MapManager 单元测试" "python tests/test_map_manager.py > /dev/null 2>&1"
run_test "FastAPI 基础功能测试" "python tests/test_basic_api.py > /dev/null 2>&1"

# 总结
echo "======================================"
echo "测试完成"
echo "======================================"
echo -e "${GREEN}通过: ${PASSED}${NC}"
echo -e "${RED}失败: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    echo ""
    echo "下一步："
    echo "  1. 启动开发服务器: make run-sim"
    echo "  2. 访问 API 文档: http://localhost:8000/docs"
    echo "  3. 健康检查: curl http://localhost:8000/health"
    exit 0
else
    echo -e "${RED}❌ 有测试失败，请检查错误信息${NC}"
    exit 1
fi
