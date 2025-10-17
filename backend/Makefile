.PHONY: help install dev test format lint run run-sim run-prod clean start stop restart pm2 supervisor docs

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help:  ## 显示帮助信息
	@echo "$(BLUE)Unitree B2 SLAM Backend - 可用命令$(NC)"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install:  ## 安装生产依赖
	@echo "$(YELLOW)📥 安装生产依赖...$(NC)"
	uv pip install -e .
	@echo "$(GREEN)✅ 生产依赖安装完成$(NC)"

dev:  ## 安装开发依赖
	@echo "$(YELLOW)📥 安装开发依赖...$(NC)"
	uv pip install -e ".[dev]"
	@echo "$(GREEN)✅ 开发依赖安装完成$(NC)"

test:  ## 运行测试
	@echo "$(YELLOW)🧪 运行测试...$(NC)"
	pytest tests/ -v --cov=backend --cov-report=term-missing

test-fast:  ## 快速测试（不生成覆盖率）
	@echo "$(YELLOW)🧪 快速测试...$(NC)"
	pytest tests/ -v

format:  ## 格式化代码
	@echo "$(YELLOW)🎨 格式化代码...$(NC)"
	black .
	@echo "$(YELLOW)🔧 修复代码风格问题...$(NC)"
	ruff check --fix .
	@echo "$(GREEN)✅ 代码格式化完成$(NC)"

lint:  ## 代码检查
	@echo "$(YELLOW)🔍 检查代码风格...$(NC)"
	ruff check .
	@echo "$(YELLOW)🔍 检查代码格式...$(NC)"
	black --check .

run:  ## 运行开发服务器（使用 .env 配置）
	@echo "$(YELLOW)🚀 启动开发服务器...$(NC)"
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-sim:  ## 运行仿真模式服务器
	@echo "$(YELLOW)🤖 启动仿真模式服务器...$(NC)"
	SIMULATOR_MODE=true uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod:  ## 运行生产模式服务器（4 workers）
	@echo "$(YELLOW)🚀 启动生产服务器...$(NC)"
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

docs:  ## 启动 API 文档服务器
	@echo "$(YELLOW)📚 API 文档地址：http://localhost:8000/docs$(NC)"
	@make run-sim

clean:  ## 清理临时文件
	@echo "$(YELLOW)🧹 清理临时文件...$(NC)"
	@bash clean.sh || (find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
		find . -type f -name "*.pyc" -delete; \
		rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info)
	@echo "$(GREEN)✅ 清理完成$(NC)"

clean-all: clean  ## 清理所有（包括虚拟环境）
	@echo "$(YELLOW)🧹 清理虚拟环境...$(NC)"
	rm -rf .venv
	@echo "$(GREEN)✅ 完全清理完成$(NC)"

start:  ## 使用启动脚本运行服务
	@echo "$(YELLOW)🚀 启动服务...$(NC)"
	@bash start.sh

pm2-start:  ## 使用 PM2 启动服务
	@echo "$(YELLOW)🚀 使用 PM2 启动服务...$(NC)"
	pm2 start pm2.config.json
	@echo "$(GREEN)✅ PM2 服务已启动$(NC)"
	@echo "$(BLUE)查看日志: pm2 logs unitree-slam-backend$(NC)"
	@echo "$(BLUE)查看状态: pm2 status$(NC)"

pm2-stop:  ## 使用 PM2 停止服务
	@echo "$(YELLOW)⏹️  停止 PM2 服务...$(NC)"
	pm2 stop unitree-slam-backend

pm2-restart:  ## 使用 PM2 重启服务
	@echo "$(YELLOW)🔄 重启 PM2 服务...$(NC)"
	pm2 restart unitree-slam-backend

pm2-logs:  ## 查看 PM2 日志
	pm2 logs unitree-slam-backend

pm2-status:  ## 查看 PM2 状态
	pm2 status

pm2-delete:  ## 删除 PM2 进程
	@echo "$(YELLOW)🗑️  删除 PM2 进程...$(NC)"
	pm2 delete unitree-slam-backend

supervisor-install:  ## 安装 Supervisor 配置
	@echo "$(YELLOW)📦 安装 Supervisor 配置...$(NC)"
	sudo cp supervisor.conf /etc/supervisor/conf.d/unitree-slam.conf
	sudo supervisorctl reread
	sudo supervisorctl update
	@echo "$(GREEN)✅ Supervisor 配置已安装$(NC)"

supervisor-start:  ## 使用 Supervisor 启动服务
	@echo "$(YELLOW)🚀 启动 Supervisor 服务...$(NC)"
	sudo supervisorctl start unitree-slam-backend

supervisor-stop:  ## 使用 Supervisor 停止服务
	@echo "$(YELLOW)⏹️  停止 Supervisor 服务...$(NC)"
	sudo supervisorctl stop unitree-slam-backend

supervisor-restart:  ## 使用 Supervisor 重启服务
	@echo "$(YELLOW)🔄 重启 Supervisor 服务...$(NC)"
	sudo supervisorctl restart unitree-slam-backend

supervisor-status:  ## 查看 Supervisor 状态
	sudo supervisorctl status unitree-slam-backend

supervisor-logs:  ## 查看 Supervisor 日志
	sudo tail -f /var/log/supervisor/unitree-slam-stdout.log

deps:  ## 显示已安装的依赖
	@echo "$(YELLOW)📦 已安装的依赖：$(NC)"
	uv pip list

deps-tree:  ## 显示依赖树
	@echo "$(YELLOW)🌳 依赖树：$(NC)"
	uv pip list --tree

deps-outdated:  ## 检查过期的依赖
	@echo "$(YELLOW)📦 检查过期依赖...$(NC)"
	uv pip list --outdated

init:  ## 初始化项目（运行 setup.sh）
	@bash setup.sh

db-init:  ## 初始化数据库目录
	@echo "$(YELLOW)📁 初始化数据目录...$(NC)"
	mkdir -p data logs
	touch data/.gitkeep logs/.gitkeep
	@echo "$(GREEN)✅ 数据目录初始化完成$(NC)"

# 快捷方式
r: run  ## run 的快捷方式
rs: run-sim  ## run-sim 的快捷方式
t: test  ## test 的快捷方式
f: format  ## format 的快捷方式
l: lint  ## lint 的快捷方式
