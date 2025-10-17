"""
状态查询相关 API

提供系统状态查询的 RESTful 接口
"""

from fastapi import APIRouter, status

from api.models import (
    GetSystemStatusResponse,
    GetOdometryResponse,
    GetCommandStatsResponse,
    ApiResponse,
)
from api.dependencies import SlamServiceDep
from api.exceptions import SlamServiceError
from logger import get_logger

logger = get_logger("api.status")

router = APIRouter(prefix="/api/status", tags=["状态查询"])


@router.get(
    "/system",
    response_model=GetSystemStatusResponse,
    summary="获取系统状态",
    description="获取 SLAM 系统当前状态",
    status_code=status.HTTP_200_OK,
)
async def get_system_status(
    slam_service: SlamServiceDep,
) -> GetSystemStatusResponse:
    """
    获取系统状态

    Args:
        slam_service: SLAM 服务实例

    Returns:
        系统状态响应
    """
    logger.debug("获取系统状态")

    try:
        system_state = slam_service.get_system_state()

        return GetSystemStatusResponse(
            success=True,
            message="系统状态查询成功",
            data={
                "state": system_state.name,
                "state_code": system_state.value,
                "description": _get_state_description(system_state.name),
            },
        )

    except Exception as e:
        logger.error(f"获取系统状态时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"获取系统状态失败: {str(e)}")


@router.get(
    "/odometry",
    response_model=GetOdometryResponse,
    summary="获取里程计数据",
    description="获取机器人当前里程计数据（位置和姿态）",
    status_code=status.HTTP_200_OK,
)
async def get_odometry(
    slam_service: SlamServiceDep,
) -> GetOdometryResponse:
    """
    获取里程计数据

    Args:
        slam_service: SLAM 服务实例

    Returns:
        里程计数据响应
    """
    logger.debug("获取里程计数据")

    try:
        odom = slam_service.get_current_odom()

        if odom is None:
            return GetOdometryResponse(
                success=False,
                message="暂无里程计数据",
                data=None,
            )

        # 提取位姿信息
        pose = odom.pose.pose
        position = pose.position
        orientation = pose.orientation

        return GetOdometryResponse(
            success=True,
            message="里程计数据查询成功",
            data={
                "position": {
                    "x": position.x,
                    "y": position.y,
                    "z": position.z,
                },
                "orientation": {
                    "qx": orientation.x,
                    "qy": orientation.y,
                    "qz": orientation.z,
                    "qw": orientation.w,
                },
            },
        )

    except Exception as e:
        logger.error(f"获取里程计数据时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"获取里程计数据失败: {str(e)}")


@router.get(
    "/commands",
    response_model=GetCommandStatsResponse,
    summary="获取命令统计",
    description="获取命令执行统计信息",
    status_code=status.HTTP_200_OK,
)
async def get_command_stats(
    slam_service: SlamServiceDep,
) -> GetCommandStatsResponse:
    """
    获取命令统计

    Args:
        slam_service: SLAM 服务实例

    Returns:
        命令统计响应
    """
    logger.debug("获取命令统计")

    try:
        stats = slam_service.get_command_statistics()

        return GetCommandStatsResponse(
            success=True,
            message="命令统计查询成功",
            data=stats,
        )

    except Exception as e:
        logger.error(f"获取命令统计时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"获取命令统计失败: {str(e)}")


@router.get(
    "/health",
    response_model=ApiResponse,
    summary="健康检查",
    description="检查服务健康状态",
    status_code=status.HTTP_200_OK,
)
async def health_check(
    slam_service: SlamServiceDep,
) -> ApiResponse:
    """
    健康检查

    Args:
        slam_service: SLAM 服务实例

    Returns:
        健康状态
    """
    try:
        # 检查 SLAM 服务是否正常
        system_state = slam_service.get_system_state()
        stats = slam_service.get_command_statistics()

        return ApiResponse(
            success=True,
            message="服务健康",
            data={
                "status": "healthy",
                "system_state": system_state.name,
                "total_commands": stats["total"],
                "pending_commands": stats["sent"],
            },
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        return ApiResponse(
            success=False,
            message=f"服务异常: {str(e)}",
            data={"status": "unhealthy"},
        )


def _get_state_description(state_name: str) -> str:
    """
    获取状态描述

    Args:
        state_name: 状态名称

    Returns:
        状态描述
    """
    descriptions = {
        "ERROR": "错误状态",
        "IDLE": "空闲状态",
        "MAPPING": "建图中",
        "NAVIGATION": "导航中",
        "RELOCATION": "重定位已开启",
        "INIT_POSE": "初始化定位完成",
        "NAV_NODE_OPEN": "导航节点已打开",
    }
    return descriptions.get(state_name, "未知状态")


__all__ = ["router"]
