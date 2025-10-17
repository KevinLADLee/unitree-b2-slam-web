"""
Unitree B2 SLAM Backend Service

FastAPI 应用入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import time

from config import config
from logger import init_logging, get_logger
from api.exceptions import register_exception_handlers

# 初始化日志
init_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("Unitree B2 SLAM Backend Service 启动中...")
    logger.info("=" * 60)

    # 打印配置
    config.print_config()

    # 确保必要的目录存在
    config.ensure_directories()

    # 初始化全局单例
    from slam.map_manager import get_map_manager
    from slam.slam_service import initialize_slam_service
    from api.websocket_manager import start_heartbeat_task

    map_manager = get_map_manager()
    logger.info(f"MapManager 已初始化: {len(map_manager)} 个地图")

    slam_service = initialize_slam_service()
    logger.info(f"SlamService 已初始化: {'仿真模式' if slam_service.simulator_mode else '真实模式'}")

    # 启动 WebSocket 心跳任务
    asyncio.create_task(start_heartbeat_task(interval=config.WS_HEARTBEAT_INTERVAL))
    logger.info(f"WebSocket 心跳任务已启动: {config.WS_HEARTBEAT_INTERVAL}s")

    logger.info("✅ 服务启动完成")
    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info("服务正在关闭...")
    logger.info("👋 服务已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title="Unitree B2 SLAM Backend",
    description="Unitree B2 SLAM 导航服务后端 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 注册异常处理器
register_exception_handlers(app)


# ============ 中间件配置 ============

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    start_time = time.time()

    # 记录请求
    logger.info(f"➡️  {request.method} {request.url.path}")

    # 处理请求
    response = await call_next(request)

    # 记录响应
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"⬅️  {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.2f}ms"
    )

    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# ============ 全局异常处理 ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if config.LOG_LEVEL == "DEBUG" else "服务器内部错误",
            "path": str(request.url.path),
        },
    )


# ============ 根路由 ============

@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "Unitree B2 SLAM Backend",
        "version": "0.1.0",
        "status": "running",
        "mode": "simulator" if config.SIMULATOR_MODE else "real",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from slam.map_manager import get_map_manager

    try:
        map_manager = get_map_manager()
        maps_count = len(map_manager)

        return {
            "status": "healthy",
            "mode": "simulator" if config.SIMULATOR_MODE else "real",
            "maps_count": maps_count,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


# ============ API 路由注册 ============

from api import mapping, navigation, relocation, topology, status, websocket

app.include_router(mapping.router)
app.include_router(navigation.router)
app.include_router(relocation.router)
app.include_router(topology.router)
app.include_router(status.router)
app.include_router(websocket.router)

logger.info("API 路由已注册")


# ============ 开发模式运行 ============

if __name__ == "__main__":
    import uvicorn

    logger.info("使用开发模式启动服务...")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower(),
    )
