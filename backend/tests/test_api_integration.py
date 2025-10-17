"""
API 端点集成测试

测试所有 RESTful API 端点的功能
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status

# 需要导入 FastAPI app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import config

# 创建 ASGI transport
transport = ASGITransport(app=app)


class TestMappingAPI:
    """建图 API 测试"""

    @pytest.mark.asyncio
    async def test_start_mapping(self):
        """测试开始建图"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/mapping/start")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "success"
            assert "index" in data["data"]
            print(f"✅ 开始建图成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_end_mapping(self):
        """测试结束建图"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开始建图
            await client.post("/api/mapping/start")
            await asyncio.sleep(1.0)

            # 结束建图
            response = await client.post(
                "/api/mapping/end",
                json={
                    "pcdmap_index": 1,
                    "save_map": True
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "success"
            print(f"✅ 结束建图成功: {data['message']}")


class TestRelocationAPI:
    """重定位 API 测试"""

    @pytest.mark.asyncio
    async def test_start_relocation(self):
        """测试开启重定位"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/relocation/start")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "success"
            print(f"✅ 开启重定位成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_init_pose(self):
        """测试初始化位姿"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开启重定位
            await client.post("/api/relocation/start")
            await asyncio.sleep(0.6)

            # 初始化位姿
            response = await client.post(
                "/api/relocation/init_pose",
                json={
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "qx": 0.0,
                    "qy": 0.0,
                    "qz": 0.0,
                    "qw": 1.0
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 初始化位姿成功: {data['message']}")


class TestNavigationAPI:
    """导航 API 测试"""

    @pytest.mark.asyncio
    async def test_start_navigation(self):
        """测试开启导航"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/navigation/start")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 开启导航成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_single_point_navigation(self):
        """测试单点导航"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开启导航
            await client.post("/api/navigation/start")
            await asyncio.sleep(0.6)

            # 单点导航
            response = await client.post(
                "/api/navigation/single_point",
                json={"target_node": 1}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 单点导航成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_loop_navigation(self):
        """测试循环导航"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开启导航
            await client.post("/api/navigation/start")
            await asyncio.sleep(0.6)

            # 循环导航
            response = await client.post(
                "/api/navigation/loop",
                json={"node_sequence": [1, 2, 3]}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 循环导航成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_pause_resume_navigation(self):
        """测试暂停/恢复导航"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 开启导航
            await client.post("/api/navigation/start")
            await asyncio.sleep(0.6)

            # 开始导航
            await client.post("/api/navigation/single_point", json={"target_node": 1})
            await asyncio.sleep(0.6)

            # 暂停导航
            response = await client.post("/api/navigation/pause")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 暂停导航成功: {data['message']}")

            await asyncio.sleep(0.6)

            # 恢复导航
            response = await client.post("/api/navigation/resume")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 恢复导航成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_return_home(self):
        """测试返回起点"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开启导航
            await client.post("/api/navigation/start")
            await asyncio.sleep(0.6)

            # 返回起点
            response = await client.post("/api/navigation/return_home")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 返回起点成功: {data['message']}")


class TestTopologyAPI:
    """拓扑图 API 测试"""

    @pytest.mark.asyncio
    async def test_add_node(self):
        """测试添加节点"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 添加节点
            response = await client.post("/api/topology/add_node")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "node" in data["data"]
            print(f"✅ 添加节点成功: 节点 {data['data']['node']['name']}")

    @pytest.mark.asyncio
    async def test_save_topology(self):
        """测试保存拓扑图"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 清除缓存
            await client.post("/api/topology/clear")

            # 添加节点
            await client.post("/api/topology/add_node")
            await asyncio.sleep(0.3)
            await client.post("/api/topology/add_node")

            # 保存拓扑图
            response = await client.post("/api/topology/save")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "nodes" in data["data"]
            assert "edges" in data["data"]
            print(f"✅ 保存拓扑图成功: {data['data']['nodes']['status']}")

    @pytest.mark.asyncio
    async def test_get_summary(self):
        """测试获取拓扑图摘要"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/topology/summary")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "node_count" in data["data"]
            assert "edge_count" in data["data"]
            print(f"✅ 获取摘要成功: {data['data']['node_count']} 个节点")

    @pytest.mark.asyncio
    async def test_delete_nodes(self):
        """测试删除节点"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 删除节点
            response = await client.delete(
                "/api/topology/nodes",
                json={"node_ids": [1]}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 删除节点成功: {data['message']}")

    @pytest.mark.asyncio
    async def test_clear_topology(self):
        """测试清除拓扑图缓存"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/topology/clear")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 清除缓存成功: {data['message']}")


class TestStatusAPI:
    """状态查询 API 测试"""

    @pytest.mark.asyncio
    async def test_get_system_status(self):
        """测试获取系统状态"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/status/system")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "state" in data["data"]
            assert "state_name" in data["data"]
            print(f"✅ 获取系统状态成功: {data['data']['state_name']}")

    @pytest.mark.asyncio
    async def test_get_odometry(self):
        """测试获取里程计数据"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 等待里程计数据生成
            await asyncio.sleep(0.5)

            response = await client.get("/api/status/odometry")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "position" in data["data"]
            assert "orientation" in data["data"]
            print(f"✅ 获取里程计成功: x={data['data']['position']['x']:.3f}")

    @pytest.mark.asyncio
    async def test_get_commands(self):
        """测试获取命令统计"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/status/commands")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "total" in data["data"]
            print(f"✅ 获取命令统计成功: 总计 {data['data']['total']} 条命令")


class TestMapRegistryAPI:
    """地图管理 API 测试"""

    @pytest.mark.asyncio
    async def test_list_maps(self):
        """测试获取地图列表"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/maps")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "maps" in data["data"]
            print(f"✅ 获取地图列表成功: {len(data['data']['maps'])} 个地图")

    @pytest.mark.asyncio
    async def test_create_map(self):
        """测试创建地图"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/maps",
                json={"map_name": "test_map_api"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["map_name"] == "test_map_api"
            assert "map_index" in data["data"]
            print(f"✅ 创建地图成功: {data['data']['map_name']} (索引: {data['data']['map_index']})")

            # 返回地图索引供后续使用
            return data["data"]["map_index"]

    @pytest.mark.asyncio
    async def test_delete_map(self):
        """测试删除地图"""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建一个地图
            create_response = await client.post(
                "/api/maps",
                json={"map_name": "test_map_to_delete"}
            )
            map_index = create_response.json()["data"]["map_index"]

            # 删除地图
            response = await client.delete(f"/api/maps/{map_index}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            print(f"✅ 删除地图成功: 索引 {map_index}")


class TestCompleteWorkflow:
    """完整工作流测试"""

    @pytest.mark.asyncio
    async def test_mapping_workflow(self):
        """测试完整建图流程"""
        print("\n" + "=" * 60)
        print("测试完整建图流程")
        print("=" * 60)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 开始建图
            print("\n1️⃣ 开始建图...")
            response = await client.post("/api/mapping/start")
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 建图已开始")

            await asyncio.sleep(1.0)

            # 2. 添加节点
            print("\n2️⃣ 添加节点...")
            await client.post("/api/topology/add_node")
            await asyncio.sleep(0.3)
            await client.post("/api/topology/add_node")
            print("   ✅ 已添加 2 个节点")

            # 3. 保存拓扑图
            print("\n3️⃣ 保存拓扑图...")
            response = await client.post("/api/topology/save")
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 拓扑图已保存")

            await asyncio.sleep(1.0)

            # 4. 结束建图
            print("\n4️⃣ 结束建图...")
            response = await client.post(
                "/api/mapping/end",
                json={"pcdmap_index": 1, "save_map": True}
            )
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 建图已结束")

            print("\n✅ 完整建图流程测试通过！")

    @pytest.mark.asyncio
    async def test_navigation_workflow(self):
        """测试完整导航流程"""
        print("\n" + "=" * 60)
        print("测试完整导航流程")
        print("=" * 60)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 准备：添加节点
            print("\n准备阶段：添加测试节点...")
            await client.post("/api/topology/clear")
            await client.post("/api/topology/add_node")
            await asyncio.sleep(0.3)
            await client.post("/api/topology/add_node")
            await asyncio.sleep(0.3)
            await client.post("/api/topology/add_node")
            await client.post("/api/topology/save")
            print("   ✅ 拓扑图准备完成")

            await asyncio.sleep(1.0)

            # 1. 开启重定位
            print("\n1️⃣ 开启重定位...")
            response = await client.post("/api/relocation/start")
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 重定位已开启")

            await asyncio.sleep(0.6)

            # 2. 初始化位姿
            print("\n2️⃣ 初始化位姿...")
            response = await client.post(
                "/api/relocation/init_pose",
                json={"x": 0.0, "y": 0.0, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
            )
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 位姿已初始化")

            await asyncio.sleep(0.6)

            # 3. 开启导航
            print("\n3️⃣ 开启导航...")
            response = await client.post("/api/navigation/start")
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 导航已开启")

            await asyncio.sleep(0.6)

            # 4. 单点导航
            print("\n4️⃣ 单点导航...")
            response = await client.post(
                "/api/navigation/single_point",
                json={"target_node": 2}
            )
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 单点导航命令已发送")

            await asyncio.sleep(1.0)

            # 5. 循环导航
            print("\n5️⃣ 循环导航...")
            response = await client.post(
                "/api/navigation/loop",
                json={"node_sequence": [1, 2, 3]}
            )
            assert response.status_code == status.HTTP_200_OK
            print("   ✅ 循环导航命令已发送")

            print("\n✅ 完整导航流程测试通过！")


async def main():
    """手动运行所有测试"""
    print("=" * 60)
    print("API 端点集成测试")
    print("=" * 60)

    # 等待服务初始化
    await asyncio.sleep(1.0)

    # 创建测试实例
    mapping_test = TestMappingAPI()
    relocation_test = TestRelocationAPI()
    navigation_test = TestNavigationAPI()
    topology_test = TestTopologyAPI()
    status_test = TestStatusAPI()
    map_test = TestMapRegistryAPI()
    workflow_test = TestCompleteWorkflow()

    try:
        # 测试建图 API
        print("\n" + "=" * 60)
        print("测试建图 API")
        print("=" * 60)
        await mapping_test.test_start_mapping()
        await asyncio.sleep(0.6)
        await mapping_test.test_end_mapping()

        # 测试重定位 API
        print("\n" + "=" * 60)
        print("测试重定位 API")
        print("=" * 60)
        await relocation_test.test_start_relocation()
        await asyncio.sleep(0.6)
        await relocation_test.test_init_pose()

        # 测试导航 API
        print("\n" + "=" * 60)
        print("测试导航 API")
        print("=" * 60)
        await navigation_test.test_start_navigation()
        await asyncio.sleep(0.6)
        await navigation_test.test_single_point_navigation()
        await asyncio.sleep(0.6)
        await navigation_test.test_loop_navigation()
        await asyncio.sleep(0.6)
        await navigation_test.test_pause_resume_navigation()
        await asyncio.sleep(0.6)
        await navigation_test.test_return_home()

        # 测试拓扑图 API
        print("\n" + "=" * 60)
        print("测试拓扑图 API")
        print("=" * 60)
        await topology_test.test_clear_topology()
        await topology_test.test_add_node()
        await asyncio.sleep(0.3)
        await topology_test.test_save_topology()
        await asyncio.sleep(0.6)
        await topology_test.test_get_summary()
        await topology_test.test_delete_nodes()
        await asyncio.sleep(0.6)
        await topology_test.test_clear_topology()

        # 测试状态 API
        print("\n" + "=" * 60)
        print("测试状态 API")
        print("=" * 60)
        await status_test.test_get_system_status()
        await status_test.test_get_odometry()
        await status_test.test_get_commands()

        # 测试地图管理 API
        print("\n" + "=" * 60)
        print("测试地图管理 API")
        print("=" * 60)
        await map_test.test_list_maps()
        await map_test.test_create_map()
        await map_test.test_delete_map()

        # 测试完整工作流
        await workflow_test.test_mapping_workflow()
        await asyncio.sleep(1.0)
        await workflow_test.test_navigation_workflow()

        print("\n" + "=" * 60)
        print("✅ 所有 API 测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
