"""
建图相关 API

提供建图的 RESTful 接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from api.models import (
    StartMappingRequest,
    StartMappingResponse,
    EndMappingRequest,
    EndMappingResponse,
    ApiResponse,
)
from api.dependencies import SlamServiceDep, MapManagerDep
from api.exceptions import (
    SlamServiceError,
    MapAlreadyExistsError,
    CommandExecutionError,
)
from slam.command_executor import CommandStatus
from logger import get_logger

logger = get_logger("api.mapping")

router = APIRouter(prefix="/api/mapping", tags=["建图"])


@router.post(
    "/start",
    response_model=StartMappingResponse,
    summary="开始建图",
    description="开始新的地图构建任务",
    status_code=status.HTTP_200_OK,
)
async def start_mapping(
    request: StartMappingRequest,
    slam_service: SlamServiceDep,
    map_manager: MapManagerDep,
) -> StartMappingResponse:
    """
    开始建图

    Args:
        request: 建图请求参数
        slam_service: SLAM 服务实例
        map_manager: 地图管理器实例

    Returns:
        建图响应

    Raises:
        MapAlreadyExistsError: 如果地图名称已存在
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(f"收到开始建图请求: map_name={request.map_name}")

    # 检查地图名称是否已存在
    if map_manager.get_index(request.map_name) is not None:
        raise MapAlreadyExistsError(f"地图名称已存在: {request.map_name}")

    # 注册地图并获取索引
    pcdmap_index = map_manager.register_map(
        map_name=request.map_name,
        description=request.description or "",
    )
    logger.info(f"注册地图: {request.map_name} -> index={pcdmap_index}")

    try:
        # 更新地图状态为 building
        map_manager.update_map_status(request.map_name, "building")

        # 发送开始建图命令
        record = await slam_service.start_mapping()

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            # 命令失败，删除已注册的地图
            map_manager.delete_map(request.map_name)
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"开始建图失败: {error_msg}")

        logger.info(f"开始建图成功: map_name={request.map_name}, index={pcdmap_index}")

        return StartMappingResponse(
            success=True,
            message="建图已开始",
            data={
                "map_name": request.map_name,
                "pcdmap_index": pcdmap_index,
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        # 重新抛出命令执行异常
        raise

    except Exception as e:
        # 其他异常，清理已注册的地图
        logger.error(f"开始建图时发生错误: {e}", exc_info=True)
        map_manager.delete_map(request.map_name)
        raise SlamServiceError(f"开始建图失败: {str(e)}")


@router.post(
    "/end",
    response_model=EndMappingResponse,
    summary="结束建图",
    description="结束当前地图构建任务并保存",
    status_code=status.HTTP_200_OK,
)
async def end_mapping(
    request: EndMappingRequest,
    slam_service: SlamServiceDep,
    map_manager: MapManagerDep,
) -> EndMappingResponse:
    """
    结束建图

    Args:
        request: 结束建图请求参数
        slam_service: SLAM 服务实例
        map_manager: 地图管理器实例

    Returns:
        结束建图响应

    Raises:
        MapNotFoundError: 如果地图不存在
        CommandExecutionError: 如果命令执行失败
    """
    logger.info(f"收到结束建图请求: map_name={request.map_name}, save={request.save_map}")

    # 获取地图索引
    pcdmap_index = map_manager.get_index(request.map_name)
    if pcdmap_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"地图不存在: {request.map_name}",
        )

    try:
        # 发送结束建图命令
        record = await slam_service.end_mapping(
            pcdmap_index=pcdmap_index,
            save=request.save_map,
        )

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"结束建图失败: {error_msg}")

        # 更新地图状态
        if request.save_map:
            map_manager.update_map_status(request.map_name, "ready")
            logger.info(f"地图已保存: {request.map_name}")
        else:
            # 如果不保存，删除地图记录
            map_manager.delete_map(request.map_name)
            logger.info(f"地图未保存，已删除记录: {request.map_name}")

        logger.info(f"结束建图成功: map_name={request.map_name}, saved={request.save_map}")

        return EndMappingResponse(
            success=True,
            message="建图已结束" if request.save_map else "建图已取消",
            data={
                "map_name": request.map_name,
                "pcdmap_index": pcdmap_index,
                "saved": request.save_map,
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        # 重新抛出命令执行异常
        raise

    except Exception as e:
        # 其他异常
        logger.error(f"结束建图时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"结束建图失败: {str(e)}")


@router.get(
    "/status/{map_name}",
    response_model=ApiResponse,
    summary="查询地图状态",
    description="查询指定地图的构建状态",
    status_code=status.HTTP_200_OK,
)
async def get_mapping_status(
    map_name: str,
    map_manager: MapManagerDep,
) -> ApiResponse:
    """
    查询地图状态

    Args:
        map_name: 地图名称
        map_manager: 地图管理器实例

    Returns:
        地图状态信息

    Raises:
        HTTPException: 如果地图不存在
    """
    logger.debug(f"查询地图状态: map_name={map_name}")

    # 获取地图信息
    map_info = map_manager.get_map_info(map_name)
    if map_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"地图不存在: {map_name}",
        )

    return ApiResponse(
        success=True,
        message="查询成功",
        data=map_info,
    )


@router.get(
    "/list",
    response_model=ApiResponse,
    summary="列出所有地图",
    description="获取所有已注册地图的列表",
    status_code=status.HTTP_200_OK,
)
async def list_maps(
    map_manager: MapManagerDep,
) -> ApiResponse:
    """
    列出所有地图

    Args:
        map_manager: 地图管理器实例

    Returns:
        地图列表
    """
    logger.debug("列出所有地图")

    maps = map_manager.list_maps()

    return ApiResponse(
        success=True,
        message=f"共有 {len(maps)} 张地图",
        data={"maps": maps, "total": len(maps)},
    )


@router.delete(
    "/{map_name}",
    response_model=ApiResponse,
    summary="删除地图",
    description="删除指定的地图记录（注意：不会删除实际地图文件）",
    status_code=status.HTTP_200_OK,
)
async def delete_map(
    map_name: str,
    map_manager: MapManagerDep,
) -> ApiResponse:
    """
    删除地图记录

    Args:
        map_name: 地图名称
        map_manager: 地图管理器实例

    Returns:
        删除结果

    Raises:
        HTTPException: 如果地图不存在
    """
    logger.info(f"删除地图: map_name={map_name}")

    # 删除地图
    success = map_manager.delete_map(map_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"地图不存在: {map_name}",
        )

    return ApiResponse(
        success=True,
        message=f"地图已删除: {map_name}",
        data={"map_name": map_name},
    )


__all__ = ["router"]
