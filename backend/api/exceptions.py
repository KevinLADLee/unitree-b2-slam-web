"""
错误处理和异常定义

定义自定义异常类和错误处理器
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from logger import get_logger

logger = get_logger("exceptions")


# ============ 自定义异常类 ============

class SlamServiceError(Exception):
    """SLAM 服务相关错误的基类"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class MapNotFoundError(SlamServiceError):
    """地图不存在"""

    def __init__(self, map_name: str):
        super().__init__(
            message=f"地图 '{map_name}' 不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
        self.map_name = map_name


class MapAlreadyExistsError(SlamServiceError):
    """地图已存在"""

    def __init__(self, map_name: str):
        super().__init__(
            message=f"地图 '{map_name}' 已存在",
            status_code=status.HTTP_409_CONFLICT,
        )
        self.map_name = map_name


class InvalidMapStateError(SlamServiceError):
    """地图状态无效"""

    def __init__(self, map_name: str, current_state: str, expected_state: str):
        super().__init__(
            message=f"地图 '{map_name}' 状态错误：当前为 '{current_state}'，期望为 '{expected_state}'",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class CommandExecutionError(SlamServiceError):
    """命令执行失败"""

    def __init__(self, command: str, reason: str):
        super().__init__(
            message=f"命令 '{command}' 执行失败: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CommandTimeoutError(SlamServiceError):
    """命令执行超时"""

    def __init__(self, command: str, timeout: int):
        super().__init__(
            message=f"命令 '{command}' 执行超时 ({timeout}秒)",
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
        )


class NodeNotFoundError(SlamServiceError):
    """节点不存在"""

    def __init__(self, node_id: int):
        super().__init__(
            message=f"节点 {node_id} 不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SimulatorError(SlamServiceError):
    """仿真器错误"""

    def __init__(self, message: str):
        super().__init__(
            message=f"仿真器错误: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============ 异常处理器 ============

async def slam_service_exception_handler(request: Request, exc: SlamServiceError):
    """SLAM 服务异常处理器"""
    logger.error(f"SLAM 服务错误: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = exc.errors()
    logger.warning(f"请求验证失败: {errors}")

    # 格式化错误信息
    formatted_errors = []
    for error in errors:
        formatted_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "请求参数验证失败",
            "details": formatted_errors,
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.warning(f"HTTP 异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "path": str(request.url.path),
        },
    )


# ============ 注册异常处理器的辅助函数 ============

def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(SlamServiceError, slam_service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    logger.info("异常处理器已注册")


__all__ = [
    "SlamServiceError",
    "MapNotFoundError",
    "MapAlreadyExistsError",
    "InvalidMapStateError",
    "CommandExecutionError",
    "CommandTimeoutError",
    "NodeNotFoundError",
    "SimulatorError",
    "register_exception_handlers",
]
