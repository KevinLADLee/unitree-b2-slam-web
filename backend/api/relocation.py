"""
重定位相关 API

提供重定位功能的 RESTful 接口
"""

from fastapi import APIRouter, status

from api.models import (
    StartRelocationRequest,
    StartRelocationResponse,
    InitPoseRequest,
    InitPoseResponse,
)
from api.dependencies import SlamServiceDep, MapManagerDep
from api.exceptions import CommandExecutionError, MapNotFoundError, SlamServiceError
from slam.command_executor import CommandStatus
from slam.command_builder import quaternion_from_euler
from logger import get_logger

logger = get_logger("api.relocation")

router = APIRouter(prefix="/api/relocation", tags=["重定位"])


@router.post(
    "/start",
    response_model=StartRelocationResponse,
    summary="开启重定位",
    description="在指定地图上开启重定位模式",
    status_code=status.HTTP_200_OK,
)
async def start_relocation(
    request: StartRelocationRequest,
    slam_service: SlamServiceDep,
    map_manager: MapManagerDep,
) -> StartRelocationResponse:
    """
    开启重定位

    Args:
        request: 开启重定位请求
        slam_service: SLAM 服务实例
        map_manager: 地图管理器实例

    Returns:
        开启重定位响应

    Raises:
        MapNotFoundError: 如果地图不存在
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(f"收到开启重定位请求: map_name={request.map_name}")

    # 验证地图是否存在
    pcdmap_index = map_manager.get_index(request.map_name)
    if pcdmap_index is None:
        raise MapNotFoundError(f"地图不存在: {request.map_name}")

    # 检查地图状态
    map_info = map_manager.get_map_info(request.map_name)
    if map_info and map_info.get("status") != "ready":
        logger.warning(f"地图状态不是 ready: {map_info.get('status')}")

    try:
        # 发送开启重定位命令
        record = await slam_service.start_relocation()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"开启重定位失败: {error_msg}")

        logger.info(f"开启重定位成功: map_name={request.map_name}")

        return StartRelocationResponse(
            success=True,
            message="重定位已开启",
            data={
                "map_name": request.map_name,
                "pcdmap_index": pcdmap_index,
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"开启重定位时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"开启重定位失败: {str(e)}")


@router.post(
    "/init-pose",
    response_model=InitPoseResponse,
    summary="初始化位姿",
    description="设置机器人的初始位姿（位置和方向）",
    status_code=status.HTTP_200_OK,
)
async def init_pose(
    request: InitPoseRequest,
    slam_service: SlamServiceDep,
) -> InitPoseResponse:
    """
    初始化位姿

    Args:
        request: 初始化位姿请求
        slam_service: SLAM 服务实例

    Returns:
        初始化位姿响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(
        f"收到初始化位姿请求: "
        f"position=({request.x}, {request.y}, {request.z})"
    )

    try:
        # 如果提供了欧拉角，转换为四元数
        if request.roll is not None or request.pitch is not None or request.yaw is not None:
            roll = request.roll or 0.0
            pitch = request.pitch or 0.0
            yaw = request.yaw or 0.0

            qx, qy, qz, qw = quaternion_from_euler(roll, pitch, yaw)

            logger.debug(
                f"欧拉角转四元数: "
                f"euler=({roll:.3f}, {pitch:.3f}, {yaw:.3f}) -> "
                f"quat=({qx:.3f}, {qy:.3f}, {qz:.3f}, {qw:.3f})"
            )
        else:
            # 使用提供的四元数
            qx = request.qx or 0.0
            qy = request.qy or 0.0
            qz = request.qz or 0.0
            qw = request.qw if request.qw is not None else 1.0

        # 发送初始化位姿命令
        record = await slam_service.init_pose(
            x=request.x,
            y=request.y,
            z=request.z,
            qx=qx,
            qy=qy,
            qz=qz,
            qw=qw,
        )

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"初始化位姿失败: {error_msg}")

        logger.info("初始化位姿成功")

        return InitPoseResponse(
            success=True,
            message="位姿初始化成功",
            data={
                "position": {"x": request.x, "y": request.y, "z": request.z},
                "orientation": {"qx": qx, "qy": qy, "qz": qz, "qw": qw},
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"初始化位姿时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"初始化位姿失败: {str(e)}")


__all__ = ["router"]
