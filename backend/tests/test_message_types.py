"""
消息类型和命令构建测试

测试 IDL 消息类型转换和命令构建功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from slam.message_types import (
    QtCommand_,
    QtNode_,
    QtEdge_,
    CommandType,
    DeleteAttribute,
    QtNotice,
    NodeAttribute,
    EdgeAttribute,
)
from slam.command_builder import CommandBuilder, quaternion_from_euler, yaw_from_quaternion
from slam.command_executor import CommandExecutor, CommandStatus
import math


def test_message_types():
    """测试消息类型定义"""
    print("\n【测试1】消息类型定义")

    # 测试 QtCommand
    cmd = QtCommand_()
    cmd.command_ = CommandType.START_MAPPING
    cmd.seq_.data = "index:123;"
    print(f"  QtCommand: command={cmd.command_}, seq={cmd.seq_.data}")
    assert cmd.command_ == 3, "START_MAPPING 应该是 3"
    print("  ✅ QtCommand 创建成功")

    # 测试 NodeAttribute
    node = NodeAttribute(node_name=1, node_x=1.0, node_y=2.0, node_z=0.0, node_yaw=0.5)
    print(f"  NodeAttribute: name={node.node_name}, pos=({node.node_x}, {node.node_y})")
    print("  ✅ NodeAttribute 创建成功")

    # 测试 EdgeAttribute
    edge = EdgeAttribute(edge_name=1, edge_start=1, edge_end=2)
    print(f"  EdgeAttribute: name={edge.edge_name}, {edge.edge_start} -> {edge.edge_end}")
    print("  ✅ EdgeAttribute 创建成功")


def test_qt_notice_parsing():
    """测试 QtNotice 解析"""
    print("\n【测试2】QtNotice 解析")

    # 测试命令反馈
    notice1 = QtNotice.parse("index:123;feedback:1;state:2;notice:建图已开始;")
    print(f"  解析1: index={notice1.index}, feedback={notice1.feedback}, notice={notice1.notice}")
    assert notice1.index == 123, "索引应该是 123"
    assert notice1.feedback == 1, "反馈应该是 1"
    assert notice1.state == 2, "状态应该是 2"
    print("  ✅ 命令反馈解析成功")

    # 测试导航反馈
    notice2 = QtNotice.parse("index:10001;arrive:3;finish:2;all:5;loop:1;obstruct:1;notice:到达节点3;")
    print(f"  解析2: arrive={notice2.arrive}, finish={notice2.finish}, all={notice2.all}")
    assert notice2.index == 10001, "导航反馈索引应该是 10001"
    assert notice2.arrive == 3, "到达节点应该是 3"
    assert notice2.finish == 2, "完成节点应该是 2"
    assert notice2.all == 5, "总节点应该是 5"
    print("  ✅ 导航反馈解析成功")


def test_command_builder():
    """测试命令构建器"""
    print("\n【测试3】命令构建器")

    # 创建命令构建器
    index_counter = 0

    def get_index():
        nonlocal index_counter
        index_counter += 1
        return index_counter

    builder = CommandBuilder(get_index)

    # 测试建图命令
    index, cmd = builder.build_start_mapping()
    print(f"  START_MAPPING: index={index}, command={cmd.command_}")
    assert cmd.command_ == CommandType.START_MAPPING
    assert cmd.seq_.data == "index:1;"
    print("  ✅ 建图命令构建成功")

    # 测试结束建图命令
    index, cmd = builder.build_end_mapping(pcdmap_index=5)
    print(f"  END_MAPPING: index={index}, pcdmap_index={cmd.pcdmap_index_}")
    assert cmd.command_ == CommandType.END_MAPPING
    assert cmd.pcdmap_index_ == [5]
    assert cmd.floor_index_ == [0]
    print("  ✅ 结束建图命令构建成功")

    # 测试导航命令
    index, cmd = builder.build_single_point_nav(target_node=3)
    print(f"  SINGLE_POINT_NAV: index={index}, target={cmd.node_edge_name_}")
    assert cmd.command_ == CommandType.SINGLE_POINT_NAV
    assert cmd.node_edge_name_ == [3]
    print("  ✅ 单点导航命令构建成功")

    # 测试循环导航（默认）
    index, cmd = builder.build_loop_navigation()
    print(f"  LOOP_NAV_DEFAULT: index={index}, command={cmd.command_}")
    assert cmd.command_ == CommandType.LOOP_NAV_DEFAULT
    print("  ✅ 默认循环导航命令构建成功")

    # 测试循环导航（自定义）
    index, cmd = builder.build_loop_navigation(node_sequence=[1, 2, 3, 4])
    print(f"  LOOP_NAV_CUSTOM: index={index}, sequence={cmd.node_edge_name_}")
    assert cmd.command_ == CommandType.LOOP_NAV_CUSTOM
    assert cmd.node_edge_name_ == [1, 2, 3, 4]
    print("  ✅ 自定义循环导航命令构建成功")

    # 测试删除命令
    index, cmd = builder.build_delete_nodes()
    print(f"  DELETE_NODES: index={index}, attribute={cmd.attribute_}")
    assert cmd.command_ == CommandType.DELETE
    assert cmd.attribute_ == DeleteAttribute.NODE
    assert cmd.node_edge_name_ == [999]
    print("  ✅ 删除节点命令构建成功")

    # 测试保存节点
    nodes = [
        NodeAttribute(1, 1.0, 2.0, 0.0, 0.5),
        NodeAttribute(2, 3.0, 4.0, 0.0, 1.0),
    ]
    index, qt_node = builder.build_save_nodes(nodes)
    print(f"  SAVE_NODES: index={index}, count={len(qt_node.node_.node_name_)}")
    assert len(qt_node.node_.node_name_) == 2
    assert qt_node.node_.node_name_ == [1, 2]
    print("  ✅ 保存节点命令构建成功")

    # 测试保存边
    edges = [
        EdgeAttribute(1, 1, 2),
        EdgeAttribute(2, 2, 3),
    ]
    index, qt_edge = builder.build_save_edges(edges)
    print(f"  SAVE_EDGES: index={index}, count={len(qt_edge.edge_.edge_name_)}")
    assert len(qt_edge.edge_.edge_name_) == 2
    assert qt_edge.edge_.start_node_name_ == [1, 2]
    print("  ✅ 保存边命令构建成功")


def test_quaternion_conversion():
    """测试四元数转换"""
    print("\n【测试4】四元数转换")

    # 测试欧拉角 -> 四元数
    roll, pitch, yaw = 0.0, 0.0, math.pi / 4  # 45度
    qx, qy, qz, qw = quaternion_from_euler(roll, pitch, yaw)
    print(f"  欧拉角 (0, 0, π/4) -> 四元数 ({qx:.3f}, {qy:.3f}, {qz:.3f}, {qw:.3f})")
    print("  ✅ 欧拉角转四元数成功")

    # 测试四元数 -> yaw
    yaw_back = yaw_from_quaternion(qx, qy, qz, qw)
    print(f"  四元数 -> Yaw: {yaw_back:.3f} (原值: {yaw:.3f})")
    assert abs(yaw_back - yaw) < 0.001, "Yaw 应该匹配"
    print("  ✅ 四元数转 Yaw 成功")


def test_command_executor():
    """测试命令执行器"""
    print("\n【测试5】命令执行器")

    executor = CommandExecutor(start_index=1, end_index=100, timeout=5)

    # 测试索引分配
    index1 = executor.get_next_index()
    index2 = executor.get_next_index()
    print(f"  分配索引: {index1}, {index2}")
    assert index1 == 1, "第一个索引应该是 1"
    assert index2 == 2, "第二个索引应该是 2"
    print("  ✅ 索引分配成功")

    # 测试命令注册
    executor.register_command(index1, "START_MAPPING")
    record = executor.get_command(index1)
    print(f"  命令记录: index={record.index}, type={record.command_type}, status={record.status}")
    assert record.status == CommandStatus.SENT, "状态应该是 SENT"
    print("  ✅ 命令注册成功")

    # 测试反馈处理
    notice = QtNotice.parse(f"index:{index1};feedback:1;state:2;notice:执行成功;")
    executor.handle_feedback(notice)
    record = executor.get_command(index1)
    print(f"  反馈后状态: {record.status}, feedback={record.feedback}")
    assert record.status == CommandStatus.SUCCESS, "状态应该是 SUCCESS"
    print("  ✅ 反馈处理成功")

    # 测试统计
    stats = executor.get_statistics()
    print(f"  统计: {stats}")
    assert stats["success"] == 1, "成功数应该是 1"
    print("  ✅ 统计功能正常")


if __name__ == "__main__":
    print("=" * 60)
    print("消息类型和命令构建测试")
    print("=" * 60)

    try:
        test_message_types()
        test_qt_notice_parsing()
        test_command_builder()
        test_quaternion_conversion()
        test_command_executor()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n【总结】")
        print("  ✅ 消息类型定义正确")
        print("  ✅ QtNotice 解析功能正常")
        print("  ✅ 命令构建器工作正常")
        print("  ✅ 四元数转换准确")
        print("  ✅ 命令执行器功能完整")
        print("")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
