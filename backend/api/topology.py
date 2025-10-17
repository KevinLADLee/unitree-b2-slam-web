"""
拓扑图相关 API

提供拓扑图管理的 RESTful 接口
"""

from fastapi import APIRouter, status
from typing import List, Optional

from api.models import (
    AddNodeRequest,
    AddNodeResponse,
    SaveTopologyResponse,
    ClearTopologyResponse,
    GetTopologyResponse,
    DeleteNodesRequest,
    DeleteNodesResponse,
    DeleteEdgesRequest,
    DeleteEdgesResponse,
    ApiResponse,
)
from api.dependencies import SlamServiceDep
from api.exceptions import CommandExecutionError, SlamServiceError
from slam.command_executor import CommandStatus
from logger import get_logger

logger = get_logger("api.topology")

router = APIRouter(prefix="/api/topology", tags=["拓扑图"])


@router.post(
    "/add-node",
    response_model=AddNodeResponse,
    summary="添加节点",
    description="基于当前里程计位置添加拓扑图节点",
    status_code=status.HTTP_200_OK,
)
async def add_node(
    request: AddNodeRequest,
    slam_service: SlamServiceDep,
) -> AddNodeResponse:
    """
    添加节点

    Args:
        request: 添加节点请求
        slam_service: SLAM 服务实例

    Returns:
        添加节点响应

    Raises:
        SlamServiceError: 如果添加节点失败
    """
    logger.info("收到添加节点请求")

    try:
        # 基于当前里程计添加节点
        node = slam_service.add_node_from_odom()

        if node is None:
            raise SlamServiceError("无法添加节点：没有里程计数据")

        logger.info(f"添加节点成功: node_id={node.node_name}")

        return AddNodeResponse(
            success=True,
            message=f"节点 {node.node_name} 已添加",
            data={
                "node_id": node.node_name,
                "position": {
                    "x": node.node_x,
                    "y": node.node_y,
                    "z": node.node_z,
                },
                "yaw": node.node_yaw,
            },
        )

    except SlamServiceError:
        raise

    except Exception as e:
        logger.error(f"添加节点时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"添加节点失败: {str(e)}")


@router.post(
    "/save",
    response_model=SaveTopologyResponse,
    summary="保存拓扑图",
    description="保存已添加的节点和边到系统",
    status_code=status.HTTP_200_OK,
)
async def save_topology(
    slam_service: SlamServiceDep,
) -> SaveTopologyResponse:
    """
    保存拓扑图

    Args:
        slam_service: SLAM 服务实例

    Returns:
        保存拓扑图响应

    Raises:
        SlamServiceError: 如果保存失败
        CommandExecutionError: 如果命令执行失败
    """
    logger.info("收到保存拓扑图请求")

    # 获取拓扑图摘要
    summary = slam_service.get_topology_summary()

    if summary["node_count"] < 2:
        raise SlamServiceError("拓扑图至少需要 2 个节点才能保存")

    try:
        # 保存拓扑图
        record_node, record_edge = await slam_service.save_topology()

        # 检查命令执行结果
        if record_node.status != CommandStatus.SUCCESS:
            error_msg = record_node.error or "命令执行失败"
            raise CommandExecutionError(f"保存节点失败: {error_msg}")

        if record_edge.status != CommandStatus.SUCCESS:
            error_msg = record_edge.error or "命令执行失败"
            raise CommandExecutionError(f"保存边失败: {error_msg}")

        logger.info(
            f"保存拓扑图成功: "
            f"{summary['node_count']} 个节点, {summary['edge_count']} 条边"
        )

        # 保存后清除本地缓存
        slam_service.clear_topology()

        return SaveTopologyResponse(
            success=True,
            message=f"拓扑图已保存：{summary['node_count']} 个节点，{summary['edge_count']} 条边",
            data={
                "node_count": summary["node_count"],
                "edge_count": summary["edge_count"],
                "command_indices": {
                    "nodes": record_node.index,
                    "edges": record_edge.index,
                },
            },
        )

    except (SlamServiceError, CommandExecutionError):
        raise

    except Exception as e:
        logger.error(f"保存拓扑图时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"保存拓扑图失败: {str(e)}")


@router.post(
    "/clear",
    response_model=ClearTopologyResponse,
    summary="清除本地拓扑图",
    description="清除本地缓存的节点和边（不影响已保存的拓扑图）",
    status_code=status.HTTP_200_OK,
)
async def clear_topology(
    slam_service: SlamServiceDep,
) -> ClearTopologyResponse:
    """
    清除本地拓扑图缓存

    Args:
        slam_service: SLAM 服务实例

    Returns:
        清除响应
    """
    logger.info("收到清除拓扑图请求")

    try:
        # 获取清除前的统计
        summary = slam_service.get_topology_summary()
        node_count = summary["node_count"]
        edge_count = summary["edge_count"]

        # 清除本地拓扑图
        slam_service.clear_topology()

        logger.info(f"清除拓扑图成功: {node_count} 个节点, {edge_count} 条边")

        return ClearTopologyResponse(
            success=True,
            message=f"已清除 {node_count} 个节点和 {edge_count} 条边",
            data={
                "cleared_nodes": node_count,
                "cleared_edges": edge_count,
            },
        )

    except Exception as e:
        logger.error(f"清除拓扑图时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"清除拓扑图失败: {str(e)}")


@router.get(
    "/summary",
    response_model=GetTopologyResponse,
    summary="获取拓扑图摘要",
    description="获取当前本地缓存的拓扑图信息",
    status_code=status.HTTP_200_OK,
)
async def get_topology_summary(
    slam_service: SlamServiceDep,
) -> GetTopologyResponse:
    """
    获取拓扑图摘要

    Args:
        slam_service: SLAM 服务实例

    Returns:
        拓扑图摘要
    """
    logger.debug("获取拓扑图摘要")

    try:
        summary = slam_service.get_topology_summary()

        return GetTopologyResponse(
            success=True,
            message=f"拓扑图包含 {summary['node_count']} 个节点和 {summary['edge_count']} 条边",
            data=summary,
        )

    except Exception as e:
        logger.error(f"获取拓扑图摘要时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"获取拓扑图摘要失败: {str(e)}")


@router.delete(
    "/nodes",
    response_model=DeleteNodesResponse,
    summary="删除节点",
    description="删除指定的节点，或删除所有节点",
    status_code=status.HTTP_200_OK,
)
async def delete_nodes(
    request: DeleteNodesRequest,
    slam_service: SlamServiceDep,
) -> DeleteNodesResponse:
    """
    删除节点

    Args:
        request: 删除节点请求
        slam_service: SLAM 服务实例

    Returns:
        删除节点响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    if request.node_ids:
        logger.info(f"收到删除节点请求: node_ids={request.node_ids}")
    else:
        logger.info("收到删除所有节点请求")

    try:
        # 发送删除节点命令
        record = await slam_service.delete_nodes(node_ids=request.node_ids)

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"删除节点失败: {error_msg}")

        if request.node_ids:
            message = f"已删除 {len(request.node_ids)} 个节点"
        else:
            message = "已删除所有节点"

        logger.info(message)

        return DeleteNodesResponse(
            success=True,
            message=message,
            data={
                "deleted_nodes": request.node_ids or [],
                "delete_all": not bool(request.node_ids),
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"删除节点时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"删除节点失败: {str(e)}")


@router.delete(
    "/edges",
    response_model=DeleteEdgesResponse,
    summary="删除边",
    description="删除指定的边，或删除所有边",
    status_code=status.HTTP_200_OK,
)
async def delete_edges(
    request: DeleteEdgesRequest,
    slam_service: SlamServiceDep,
) -> DeleteEdgesResponse:
    """
    删除边

    Args:
        request: 删除边请求
        slam_service: SLAM 服务实例

    Returns:
        删除边响应

    Raises:
        CommandExecutionError: 如果命令执行失败
    """
    if request.edge_ids:
        logger.info(f"收到删除边请求: edge_ids={request.edge_ids}")
    else:
        logger.info("收到删除所有边请求")

    try:
        # 发送删除边命令
        record = await slam_service.delete_edges(edge_ids=request.edge_ids)

        # 检查命令执行结果
        if record.status != CommandStatus.SUCCESS:
            error_msg = record.error or "命令执行失败"
            raise CommandExecutionError(f"删除边失败: {error_msg}")

        if request.edge_ids:
            message = f"已删除 {len(request.edge_ids)} 条边"
        else:
            message = "已删除所有边"

        logger.info(message)

        return DeleteEdgesResponse(
            success=True,
            message=message,
            data={
                "deleted_edges": request.edge_ids or [],
                "delete_all": not bool(request.edge_ids),
                "command_index": record.index,
            },
        )

    except CommandExecutionError:
        raise

    except Exception as e:
        logger.error(f"删除边时发生错误: {e}", exc_info=True)
        raise SlamServiceError(f"删除边失败: {str(e)}")


__all__ = ["router"]
