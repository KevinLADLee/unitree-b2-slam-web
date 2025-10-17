#!/bin/bash
#
# 清理脚本 - 清理 Python 缓存文件和临时文件
#

echo "🧹 清理 Python 缓存文件..."

# 清理 __pycache__ 目录
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 清理 .pyc 文件
find . -type f -name "*.pyc" -delete

# 清理 .pyo 文件
find . -type f -name "*.pyo" -delete

# 清理 pytest 缓存
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# 清理 mypy 缓存
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null

# 清理 ruff 缓存
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null

# 清理临时文件
find . -type f -name "*.tmp" -delete
find . -type f -name "*.log.*" -delete

echo "✅ 清理完成！"
