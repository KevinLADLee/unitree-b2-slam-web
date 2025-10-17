"""
导航相关 API

提供导航控制的 RESTful 接口
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from api.models import (
    StartNavigationRequest,
    StartNavigationResponse,
    SinglePointNavRequest,
    SinglePointNavResponse,
    LoopNavRequest,
    LoopNavigationResponse,
    PauseNavigationResponse,
    ResumeNavigationResponse,
    ReturnHomeResponse,
    ApiResponse,
)
from api.dependencies import SlamServiceDep, MapManagerDep
from api.exceptions import CommandExecutionError, MapNotFoundError, SlamServiceError
from slam.command_executor import CommandStatus
from logger import get_logger

logger = get_logger("api.navigation")

router = APIRouter(prefix="/api/navigation", tags=["导航"])


@router.post(
    "/start",
    response_model=StartNavigationResponse,
    summary="开启导航",
    description="开启导航模式，需要先进行重定位",
    status_code=status.HTTP_200_OK,
)
async def start_navigation(
    request: StartNavigationRequest,
    slam_service: SlamServiceDep,
    map_manager: MapManagerDep,
) -> StartNavigationResponse:
    """
    开启导航

    Args:
        request: 开启导航请求
        slam_service: SLAM 服务实例
        map_manager: 地图管理器实例

    Returns:
        开启导航响应

    Raises:
        MapNotFoundError: 如果地图不存在
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(f"收到开启导航请求: map_name={request.map_name}")

    # 验证地图是否存在
    pcdmap_index = map_manager.get_index(request.map_name)
    if pcdmap_index is None:
        raise MapNotFoundError(f"地图不存在: {request.map_name}")

    try:
        # 发送开启导航命令
        record = await slam_service.start_navigation()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"开启导航失败: {error_msg}")

        logger.info(f"开启导航成功: map_name={request.map_name}")

        return StartNavigationResponse(
            success=True,
            message="导航已开启",
            data={
                "map_name": request.map_name,
                "pcdmap_index": pcdmap_index,
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"开启导航时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"开启导航失败: {str(e)}")


@router.post(
    "/single-point",
    response_model=SinglePointNavResponse,
    summary="单点导航",
    description="导航到指定的目标节点",
    status_code=status.HTTP_200_OK,
)
async def single_point_navigation(
    request: SinglePointNavRequest,
    slam_service: SlamServiceDep,
) -> SinglePointNavResponse:
    """
    单点导航

    Args:
        request: 单点导航请求
        slam_service: SLAM 服务实例

    Returns:
        单点导航响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(f"收到单点导航请求: target_node={request.target_node}")

    try:
        # 发送单点导航命令
        record = await slam_service.single_point_nav(target_node=request.target_node)

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"单点导航失败: {error_msg}")

        logger.info(f"单点导航成功: target_node={request.target_node}")

        return SinglePointNavResponse(
            success=True,
            message=f"开始导航到节点 {request.target_node}",
            data={
                "target_node": request.target_node,
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"单点导航时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"单点导航失败: {str(e)}")


@router.post(
    "/loop",
    response_model=LoopNavigationResponse,
    summary="循环导航",
    description="按照指定节点序列循环导航，或使用默认路径",
    status_code=status.HTTP_200_OK,
)
async def loop_navigation(
    request: LoopNavRequest,
    slam_service: SlamServiceDep,
) -> LoopNavigationResponse:
    """
    循环导航

    Args:
        request: 循环导航请求
        slam_service: SLAM 服务实例

    Returns:
        循环导航响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    if request.node_sequence:
        logger.info(f"收到循环导航请求: node_sequence={request.node_sequence}")
    else:
        logger.info("收到默认循环导航请求")

    try:
        # 发送循环导航命令
        record = await slam_service.loop_navigation(node_sequence=request.node_sequence)

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"循环导航失败: {error_msg}")

        logger.info("循环导航成功")

        return LoopNavigationResponse(
            success=True,
            message="循环导航已开始",
            data={
                "node_sequence": request.node_sequence or [],
                "mode": "custom" if request.node_sequence else "default",
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"循环导航时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"循环导航失败: {str(e)}")


@router.post(
    "/pause",
    response_model=PauseNavigationResponse,
    summary="暂停导航",
    description="暂停当前导航任务",
    status_code=status.HTTP_200_OK,
)
async def pause_navigation(
    slam_service: SlamServiceDep,
) -> PauseNavigationResponse:
    """
    暂停导航

    Args:
        slam_service: SLAM 服务实例

    Returns:
        暂停导航响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    logger.info("收到暂停导航请求")

    try:
        # 发送暂停导航命令
        record = await slam_service.pause_navigation()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"暂停导航失败: {error_msg}")

        logger.info("暂停导航成功")

        return PauseNavigationResponse(
            success=True,
            message="导航已暂停",
            data={"command_index": record.index},
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"暂停导航时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"暂停导航失败: {str(e)}")


@router.post(
    "/resume",
    response_model=ResumeNavigationResponse,
    summary="恢复导航",
    description="恢复暂停的导航任务",
    status_code=status.HTTP_200_OK,
)
async def resume_navigation(
    slam_service: SlamServiceDep,
) -> ResumeNavigationResponse:
    """
    恢复导航

    Args:
        slam_service: SLAM 服务实例

    Returns:
        恢复导航响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    logger.info("收到恢复导航请求")

    try:
        # 发送恢复导航命令
        record = await slam_service.resume_navigation()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"恢复导航失败: {error_msg}")

        logger.info("恢复导航成功")

        return ResumeNavigationResponse(
            success=True,
            message="导航已恢复",
            data={"command_index": record.index},
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"恢复导航时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"恢复导航失败: {str(e)}")


@router.post(
    "/return-home",
    response_model=ReturnHomeResponse,
    summary="返回起点",
    description="导航返回起始位置",
    status_code=status.HTTP_200_OK,
)
async def return_home(
    slam_service: SlamServiceDep,
) -> ReturnHomeResponse:
    """
    返回起点

    Args:
        slam_service: SLAM 服务实例

    Returns:
        返回起点响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    logger.info("收到返回起点请求")

    try:
        # 发送返回起点命令
        record = await slam_service.return_home()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"返回起点失败: {error_msg}")

        logger.info("返回起点成功")

        return ReturnHomeResponse(
            success=True,
            message="开始返回起点",
            data={"command_index": record.index},
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"返回起点时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"返回起点失败: {str(e)}")


__all__ = ["router"]
