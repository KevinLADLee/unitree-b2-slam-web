"""
SLAM 服务测试

测试 SlamService 的核心功能
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from slam.slam_service import (
    SlamService,
    SimPublisher,
    SimSubscriber,
)
from slam.message_types import (
    QtNotice,
    Odometry_,
    PoseWithCovariance,
    Pose,
    Point,
    Quaternion,
    String_,
    SystemState,
    CommandFeedback,
)
from slam.command_executor import CommandStatus


def test_publisher_subscriber():
    """测试发布器和订阅器"""
    print("\n【测试1】发布器和订阅器")

    # 测试仿真发布器
    pub = SimPublisher("test_topic", String_)
    pub.init()
    print("  ✅ SimPublisher 初始化成功")

    msg = String_(data="test message")
    pub.write(msg)
    print("  ✅ SimPublisher 发布消息成功")

    # 测试仿真订阅器
    received = []

    def callback(msg):
        received.append(msg)

    sub = SimSubscriber("test_topic", String_)
    sub.init(callback)
    print("  ✅ SimSubscriber 初始化成功")

    # 手动触发回调
    test_msg = String_(data="callback test")
    sub.trigger_callback(test_msg)
    assert len(received) == 1, "应该收到 1 条消息"
    assert received[0].data == "callback test", "消息内容应该匹配"
    print("  ✅ SimSubscriber 回调触发成功")


def test_slam_service_init():
    """测试 SLAM 服务初始化"""
    print("\n【测试2】SLAM 服务初始化")

    # 仿真模式初始化
    service = SlamService(simulator_mode=True)
    print("  ✅ SlamService 初始化成功（仿真模式）")

    # 检查初始状态
    assert service.get_system_state() == SystemState.IDLE, "初始状态应该是 IDLE"
    assert service.get_current_odom() is None, "初始里程计应该为 None"
    print("  ✅ 初始状态检查通过")

    # 检查命令执行器
    stats = service.get_command_statistics()
    assert stats["total"] == 0, "初始命令数应该为 0"
    print("  ✅ 命令执行器初始化成功")


def test_odometry_handling():
    """测试里程计处理"""
    print("\n【测试3】里程计处理")

    service = SlamService(simulator_mode=True)

    # 创建测试里程计消息
    odom = Odometry_()
    odom.pose = PoseWithCovariance()
    odom.pose.pose = Pose()
    odom.pose.pose.position = Point(x=1.0, y=2.0, z=0.0)
    odom.pose.pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

    # 触发回调
    service._odometry_handler(odom)

    # 检查里程计是否更新
    current_odom = service.get_current_odom()
    assert current_odom is not None, "里程计应该已更新"
    assert current_odom.pose.pose.position.x == 1.0, "X 坐标应该是 1.0"
    assert current_odom.pose.pose.position.y == 2.0, "Y 坐标应该是 2.0"
    print("  ✅ 里程计更新成功")

    # 测试回调注册
    callback_triggered = []

    def odom_callback(msg):
        callback_triggered.append(msg)

    service.register_odom_callback(odom_callback)
    service._odometry_handler(odom)

    assert len(callback_triggered) == 1, "回调应该被触发 1 次"
    print("  ✅ 里程计回调注册成功")


def test_notice_handling():
    """测试 qt_notice 处理"""
    print("\n【测试4】Qt Notice 处理")

    service = SlamService(simulator_mode=True)

    # 测试回调注册
    callback_triggered = []

    def notice_callback(qt_notice: QtNotice):
        callback_triggered.append(qt_notice)

    service.register_notice_callback(notice_callback)

    # 创建测试 notice 消息
    notice_str = String_(data="index:1;feedback:1;state:2;notice:建图已开始;")
    service._qt_notice_handler(notice_str)

    # 检查回调是否触发
    assert len(callback_triggered) == 1, "回调应该被触发 1 次"
    qt_notice = callback_triggered[0]
    assert qt_notice.index == 1, "索引应该是 1"
    assert qt_notice.feedback == 1, "反馈应该是 1"
    assert qt_notice.state == 2, "状态应该是 2"
    print("  ✅ Notice 回调触发成功")

    # 检查系统状态更新
    assert service.get_system_state() == SystemState.MAPPING, "系统状态应该更新为 MAPPING"
    print("  ✅ 系统状态更新成功")


async def test_mapping_commands():
    """测试建图命令"""
    print("\n【测试5】建图命令")

    service = SlamService(simulator_mode=True)

    # 开始建图
    task = asyncio.create_task(service.start_mapping())

    # 模拟反馈
    await asyncio.sleep(0.1)
    notice_str = String_(data="index:1;feedback:1;state:2;notice:建图已开始;")
    service._qt_notice_handler(notice_str)

    # 等待命令完成
    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    assert record.command_type == "START_MAPPING", "命令类型应该是 START_MAPPING"
    print("  ✅ 开始建图命令成功")

    # 结束建图
    task = asyncio.create_task(service.end_mapping(pcdmap_index=1))

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:2;feedback:1;state:0;notice:建图已结束;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    assert record.command_type == "END_MAPPING", "命令类型应该是 END_MAPPING"
    print("  ✅ 结束建图命令成功")


async def test_navigation_commands():
    """测试导航命令"""
    print("\n【测试6】导航命令")

    service = SlamService(simulator_mode=True)

    # 开启导航
    task = asyncio.create_task(service.start_navigation())

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:1;feedback:1;state:6;notice:导航已开启;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 开启导航命令成功")

    # 单点导航
    task = asyncio.create_task(service.single_point_nav(target_node=3))

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:2;feedback:1;state:3;notice:开始导航到节点3;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 单点导航命令成功")

    # 循环导航
    task = asyncio.create_task(service.loop_navigation([1, 2, 3, 4]))

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:3;feedback:1;state:3;notice:开始循环导航;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 循环导航命令成功")


async def test_relocation_commands():
    """测试重定位命令"""
    print("\n【测试7】重定位命令")

    service = SlamService(simulator_mode=True)

    # 开启重定位
    task = asyncio.create_task(service.start_relocation())

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:1;feedback:1;state:4;notice:重定位已开启;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 开启重定位命令成功")

    # 初始化位姿
    task = asyncio.create_task(service.init_pose(x=1.0, y=2.0, z=0.0))

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:2;feedback:1;state:5;notice:初始化位姿成功;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 初始化位姿命令成功")


def test_topology_operations():
    """测试拓扑图操作"""
    print("\n【测试8】拓扑图操作")

    service = SlamService(simulator_mode=True)

    # 设置测试里程计
    odom = Odometry_()
    odom.pose = PoseWithCovariance()
    odom.pose.pose = Pose()
    odom.pose.pose.position = Point(x=1.0, y=2.0, z=0.0)
    odom.pose.pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
    service._odometry_handler(odom)

    # 添加第一个节点
    node1 = service.add_node_from_odom()
    assert node1 is not None, "应该成功添加节点"
    assert node1.node_name == 1, "节点名称应该是 1"
    print("  ✅ 添加第一个节点成功")

    # 添加第二个节点
    odom.pose.pose.position.x = 3.0
    service._odometry_handler(odom)
    node2 = service.add_node_from_odom()
    assert node2.node_name == 2, "节点名称应该是 2"
    print("  ✅ 添加第二个节点成功")

    # 检查拓扑图摘要
    summary = service.get_topology_summary()
    assert summary["node_count"] == 2, "应该有 2 个节点"
    assert summary["edge_count"] == 1, "应该有 1 条边"
    print("  ✅ 拓扑图摘要正确")

    # 清除拓扑图
    service.clear_topology()
    summary = service.get_topology_summary()
    assert summary["node_count"] == 0, "节点数应该为 0"
    assert summary["edge_count"] == 0, "边数应该为 0"
    print("  ✅ 清除拓扑图成功")


async def test_delete_commands():
    """测试删除命令"""
    print("\n【测试9】删除命令")

    service = SlamService(simulator_mode=True)

    # 删除所有节点
    task = asyncio.create_task(service.delete_nodes())

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:1;feedback:1;state:0;notice:已删除所有节点;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 删除所有节点命令成功")

    # 删除所有边
    task = asyncio.create_task(service.delete_edges())

    await asyncio.sleep(0.1)
    notice_str = String_(data="index:2;feedback:1;state:0;notice:已删除所有边;")
    service._qt_notice_handler(notice_str)

    record = await task
    assert record.status == CommandStatus.SUCCESS, "命令应该成功"
    print("  ✅ 删除所有边命令成功")


async def test_command_statistics():
    """测试命令统计"""
    print("\n【测试10】命令统计")

    service = SlamService(simulator_mode=True)

    # 发送几个命令
    task1 = asyncio.create_task(service.start_mapping())
    task2 = asyncio.create_task(service.start_navigation())

    await asyncio.sleep(0.1)

    # 检查统计
    stats = service.get_command_statistics()
    assert stats["total"] == 2, "总命令数应该是 2"
    assert stats["sent"] == 2, "已发送命令数应该是 2"
    print(f"  统计信息: {stats}")
    print("  ✅ 命令统计正确")

    # 模拟反馈
    notice_str1 = String_(data="index:1;feedback:1;state:2;notice:建图已开始;")
    service._qt_notice_handler(notice_str1)

    notice_str2 = String_(data="index:2;feedback:1;state:6;notice:导航已开启;")
    service._qt_notice_handler(notice_str2)

    await task1
    await task2

    # 检查更新后的统计
    stats = service.get_command_statistics()
    assert stats["success"] == 2, "成功命令数应该是 2"
    print(f"  更新后统计: {stats}")
    print("  ✅ 命令统计更新正确")


if __name__ == "__main__":
    print("=" * 60)
    print("SLAM 服务测试")
    print("=" * 60)

    try:
        # 同步测试
        test_publisher_subscriber()
        test_slam_service_init()
        test_odometry_handling()
        test_notice_handling()
        test_topology_operations()

        # 异步测试
        asyncio.run(test_mapping_commands())
        asyncio.run(test_navigation_commands())
        asyncio.run(test_relocation_commands())
        asyncio.run(test_delete_commands())
        asyncio.run(test_command_statistics())

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n【总结】")
        print("  ✅ Publisher/Subscriber 工作正常")
        print("  ✅ SLAM 服务初始化成功")
        print("  ✅ 里程计处理正常")
        print("  ✅ Notice 处理正常")
        print("  ✅ 建图命令功能完整")
        print("  ✅ 导航命令功能完整")
        print("  ✅ 重定位命令功能完整")
        print("  ✅ 拓扑图操作正常")
        print("  ✅ 删除命令功能完整")
        print("  ✅ 命令统计功能正常")
        print("")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
