"""
仿真器集成测试

测试仿真模块与 SLAM 服务的集成
"""

import asyncio
import pytest
from typing import List

from slam.slam_service import SlamService
from slam.message_types import QtNotice, Odometry_
from simulator import get_simulator_manager, initialize_simulator_manager


class TestSimulatorIntegration:
    """仿真器集成测试"""

    @pytest.fixture
    def slam_service(self):
        """创建仿真模式的 SLAM 服务"""
        service = SlamService(simulator_mode=True)
        yield service
        # 清理
        # Note: 可能需要添加清理逻辑

    @pytest.mark.asyncio
    async def test_simulator_initialization(self, slam_service):
        """测试仿真器初始化"""
        assert slam_service.simulator_mode is True
        assert slam_service._simulator is not None
        print("✅ 仿真器初始化成功")

    @pytest.mark.asyncio
    async def test_odometry_generation(self, slam_service):
        """测试里程计数据生成"""
        # 注册回调收集数据
        odom_data: List[Odometry_] = []

        def collect_odom(odom: Odometry_):
            odom_data.append(odom)
            print(f"📍 收到里程计: x={odom.pose.pose.position.x:.3f}, "
                  f"y={odom.pose.pose.position.y:.3f}, "
                  f"z={odom.pose.pose.position.z:.3f}")

        slam_service.register_odom_callback(collect_odom)

        # 等待接收数据
        print("\n⏳ 等待里程计数据...")
        await asyncio.sleep(2.0)

        # 验证
        assert len(odom_data) >= 10, f"期望至少收到 10 条数据，实际收到 {len(odom_data)} 条"
        print(f"✅ 成功接收 {len(odom_data)} 条里程计数据")

    @pytest.mark.asyncio
    async def test_command_response(self, slam_service):
        """测试命令响应"""
        # 注册回调收集 notice
        notices: List[QtNotice] = []

        def collect_notice(notice: QtNotice):
            notices.append(notice)
            print(f"📢 收到 Notice: feedback={notice.feedback}, "
                  f"state={notice.state}, notice={notice.notice}")

        slam_service.register_notice_callback(collect_notice)

        # 发送开始建图命令
        print("\n🗺️  发送开始建图命令...")
        record = await slam_service.start_mapping()

        # 验证
        assert record.status.value == "success", f"命令失败: {record.error}"
        assert len(notices) >= 1, "没有收到 notice 响应"
        print(f"✅ 命令执行成功: {record.command_type}")
        print(f"   - 响应时间: {(record.response_time - record.sent_time):.3f}s")
        print(f"   - Notice: {notices[-1].notice}")

    @pytest.mark.asyncio
    async def test_mapping_workflow(self, slam_service):
        """测试建图工作流"""
        notices: List[QtNotice] = []
        slam_service.register_notice_callback(lambda n: notices.append(n))

        print("\n🗺️  测试建图工作流...")

        # 1. 开始建图
        print("1️⃣ 开始建图...")
        record = await slam_service.start_mapping()
        assert record.status.value == "success"
        assert slam_service.get_system_state().value == 2  # MAPPING
        print("   ✅ 建图已开始")

        # 2. 等待一段时间（模拟建图过程）
        await asyncio.sleep(1.0)

        # 3. 添加节点
        print("2️⃣ 添加节点...")
        node1 = slam_service.add_node_from_odom()
        assert node1 is not None
        print(f"   ✅ 节点 {node1.node_name} 已添加")

        # 设置新位置
        slam_service._simulator.set_robot_pose(1.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.5)

        node2 = slam_service.add_node_from_odom()
        assert node2 is not None
        print(f"   ✅ 节点 {node2.node_name} 已添加")

        # 4. 保存拓扑图
        print("3️⃣ 保存拓扑图...")
        record_node, record_edge = await slam_service.save_topology()
        assert record_node.status.value == "success"
        assert record_edge.status.value == "success"
        print("   ✅ 拓扑图已保存")

        # 5. 结束建图
        print("4️⃣ 结束建图...")
        record = await slam_service.end_mapping(pcdmap_index=1, save=True)
        assert record.status.value == "success"
        assert slam_service.get_system_state().value == 0  # IDLE
        print("   ✅ 建图已结束")

        print(f"\n✅ 建图工作流测试完成，共收到 {len(notices)} 条通知")

    @pytest.mark.asyncio
    async def test_navigation_workflow(self, slam_service):
        """测试导航工作流"""
        notices: List[QtNotice] = []
        slam_service.register_notice_callback(lambda n: notices.append(n))

        print("\n🚗 测试导航工作流...")

        # 清除之前的拓扑图
        slam_service.clear_topology()

        # 准备：添加节点
        print("准备阶段：添加测试节点...")
        slam_service._simulator.set_robot_pose(0.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.3)
        node1 = slam_service.add_node_from_odom()

        slam_service._simulator.set_robot_pose(1.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.3)
        node2 = slam_service.add_node_from_odom()

        slam_service._simulator.set_robot_pose(1.0, 1.0, 0.0, 0.0)
        await asyncio.sleep(0.3)
        node3 = slam_service.add_node_from_odom()

        await slam_service.save_topology()
        print("   ✅ 拓扑图准备完成")

        # 1. 开启重定位
        print("1️⃣ 开启重定位...")
        record = await slam_service.start_relocation()
        assert record.status.value == "success"
        print("   ✅ 重定位已开启")

        # 2. 初始化位姿
        print("2️⃣ 初始化位姿...")
        record = await slam_service.init_pose(0.0, 0.0, 0.0)
        assert record.status.value == "success"
        print("   ✅ 位姿已初始化")

        # 3. 开启导航
        print("3️⃣ 开启导航...")
        record = await slam_service.start_navigation()
        assert record.status.value == "success"
        print("   ✅ 导航已开启")

        # 4. 单点导航
        print("4️⃣ 单点导航...")
        record = await slam_service.single_point_nav(target_node=2)
        assert record.status.value == "success"
        print("   ✅ 单点导航命令已发送")

        # 等待导航完成通知
        await asyncio.sleep(2.5)

        # 5. 循环导航
        print("5️⃣ 循环导航...")
        record = await slam_service.loop_navigation(node_sequence=[1, 2, 3])
        assert record.status.value == "success"
        print("   ✅ 循环导航命令已发送")

        await asyncio.sleep(1.0)

        # 6. 暂停导航
        print("6️⃣ 暂停导航...")
        record = await slam_service.pause_navigation()
        assert record.status.value == "success"
        print("   ✅ 导航已暂停")

        # 7. 恢复导航
        print("7️⃣ 恢复导航...")
        record = await slam_service.resume_navigation()
        assert record.status.value == "success"
        print("   ✅ 导航已恢复")

        print(f"\n✅ 导航工作流测试完成，共收到 {len(notices)} 条通知")

    @pytest.mark.asyncio
    async def test_topology_operations(self, slam_service):
        """测试拓扑图操作"""
        print("\n🗺️  测试拓扑图操作...")

        # 清除之前的拓扑图
        slam_service.clear_topology()

        # 1. 添加节点
        print("1️⃣ 添加节点...")
        slam_service._simulator.set_robot_pose(0.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.2)
        node1 = slam_service.add_node_from_odom()

        slam_service._simulator.set_robot_pose(1.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.2)
        node2 = slam_service.add_node_from_odom()

        slam_service._simulator.set_robot_pose(2.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.2)
        node3 = slam_service.add_node_from_odom()

        # 检查拓扑图摘要
        summary = slam_service.get_topology_summary()
        assert summary["node_count"] == 3
        assert summary["edge_count"] == 2
        print(f"   ✅ 添加了 {summary['node_count']} 个节点和 {summary['edge_count']} 条边")

        # 2. 保存拓扑图
        print("2️⃣ 保存拓扑图...")
        record_node, record_edge = await slam_service.save_topology()
        assert record_node.status.value == "success"
        assert record_edge.status.value == "success"

        # 验证仿真器中保存的数据
        saved_topology = slam_service._simulator.get_saved_topology()
        assert len(saved_topology["nodes"]) == 3
        assert len(saved_topology["edges"]) == 2
        print("   ✅ 拓扑图已保存到仿真器")

        # 3. 删除节点
        print("3️⃣ 删除节点...")
        record = await slam_service.delete_nodes([2])
        assert record.status.value == "success"
        print("   ✅ 节点 2 已删除")

        # 4. 删除所有边
        print("4️⃣ 删除所有边...")
        record = await slam_service.delete_edges(None)
        assert record.status.value == "success"
        print("   ✅ 所有边已删除")

        # 5. 清除本地缓存
        print("5️⃣ 清除本地缓存...")
        slam_service.clear_topology()
        summary = slam_service.get_topology_summary()
        assert summary["node_count"] == 0
        assert summary["edge_count"] == 0
        print("   ✅ 本地缓存已清除")

        print("\n✅ 拓扑图操作测试完成")

    @pytest.mark.asyncio
    async def test_robot_movement(self, slam_service):
        """测试机器人移动"""
        print("\n🤖 测试机器人移动...")

        # 设置初始位置
        slam_service._simulator.set_robot_pose(0.0, 0.0, 0.0, 0.0)
        await asyncio.sleep(0.2)

        # 获取初始位置
        x, y, z, yaw = slam_service._simulator.get_current_pose()
        print(f"初始位置: ({x:.2f}, {y:.2f}, {z:.2f}), yaw={yaw:.2f}")
        assert abs(x) < 0.1 and abs(y) < 0.1

        # 移动到新位置
        print("移动到 (2.0, 3.0)...")
        slam_service._simulator.move_robot_to(2.0, 3.0, speed=1.0)

        # 等待移动（观察里程计变化）
        for i in range(10):
            await asyncio.sleep(0.3)
            x, y, z, yaw = slam_service._simulator.get_current_pose()
            print(f"  [{i+1}] 当前位置: ({x:.2f}, {y:.2f}), yaw={yaw:.2f}")

            if slam_service._simulator.is_robot_at(2.0, 3.0, tolerance=0.2):
                print(f"✅ 已到达目标位置")
                break

        print("\n✅ 机器人移动测试完成")


async def main():
    """手动运行测试"""
    print("=" * 60)
    print("仿真器集成测试")
    print("=" * 60)

    # 创建仿真服务
    print("\n初始化仿真服务...")
    service = SlamService(simulator_mode=True)
    print("✅ 仿真服务初始化完成\n")

    # 等待仿真器启动
    await asyncio.sleep(0.5)

    # 创建测试实例
    test = TestSimulatorIntegration()

    try:
        # 运行测试
        print("\n" + "=" * 60)
        print("测试 1: 仿真器初始化")
        print("=" * 60)
        await test.test_simulator_initialization(service)

        print("\n" + "=" * 60)
        print("测试 2: 里程计数据生成")
        print("=" * 60)
        await test.test_odometry_generation(service)

        print("\n" + "=" * 60)
        print("测试 3: 命令响应")
        print("=" * 60)
        await test.test_command_response(service)

        print("\n" + "=" * 60)
        print("测试 4: 建图工作流")
        print("=" * 60)
        await test.test_mapping_workflow(service)

        print("\n" + "=" * 60)
        print("测试 5: 拓扑图操作")
        print("=" * 60)
        await test.test_topology_operations(service)

        print("\n" + "=" * 60)
        print("测试 6: 导航工作流")
        print("=" * 60)
        await test.test_navigation_workflow(service)

        print("\n" + "=" * 60)
        print("测试 7: 机器人移动")
        print("=" * 60)
        await test.test_robot_movement(service)

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
