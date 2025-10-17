"""
MapManager 测试

快速验证 MapManager 功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from slam.map_manager import MapManager


def test_map_manager():
    """测试 MapManager 基本功能"""
    print("=" * 60)
    print("测试 MapManager 功能")
    print("=" * 60)

    # 使用测试存储路径
    manager = MapManager("./data/test_map_registry.json")

    # 清空现有数据
    manager.clear()
    print("\n✅ 已清空现有数据")

    # 测试1: 注册新地图
    print("\n【测试1】注册新地图")
    index1 = manager.register_map("warehouse_floor1", "仓库一楼地图")
    print(f"  注册 'warehouse_floor1' -> 索引 {index1}")
    assert index1 == 1, "第一个地图索引应该是 1"

    index2 = manager.register_map("office_map", "办公区域地图")
    print(f"  注册 'office_map' -> 索引 {index2}")
    assert index2 == 2, "第二个地图索引应该是 2"

    # 测试2: 重复注册（应返回现有索引）
    print("\n【测试2】重复注册")
    index3 = manager.register_map("warehouse_floor1", "重复注册")
    print(f"  重复注册 'warehouse_floor1' -> 索引 {index3}")
    assert index3 == 1, "重复注册应返回现有索引"

    # 测试3: 查询索引
    print("\n【测试3】查询索引")
    found_index = manager.get_index("office_map")
    print(f"  查询 'office_map' -> 索引 {found_index}")
    assert found_index == 2, "应该找到正确的索引"

    not_found = manager.get_index("nonexistent")
    print(f"  查询 'nonexistent' -> {not_found}")
    assert not_found is None, "不存在的地图应返回 None"

    # 测试4: 查询名称
    print("\n【测试4】查询名称")
    found_name = manager.get_name(1)
    print(f"  查询索引 1 -> '{found_name}'")
    assert found_name == "warehouse_floor1", "应该找到正确的名称"

    # 测试5: 更新状态
    print("\n【测试5】更新地图状态")
    manager.update_map_status("warehouse_floor1", "completed")
    print(f"  更新 'warehouse_floor1' 状态为 'completed'")
    metadata = manager.get_metadata("warehouse_floor1")
    print(f"  当前状态: {metadata['status']}")
    assert metadata["status"] == "completed", "状态应该更新为 completed"

    # 测试6: 列出所有地图
    print("\n【测试6】列出所有地图")
    maps = manager.list_maps()
    print(f"  共 {len(maps)} 个地图:")
    for m in maps:
        print(f"    - {m['name']} (索引={m['index']}, 状态={m.get('status', 'N/A')})")
    assert len(maps) == 2, "应该有 2 个地图"

    # 测试7: 删除地图
    print("\n【测试7】删除地图")
    success = manager.delete_map("office_map")
    print(f"  删除 'office_map': {'成功' if success else '失败'}")
    assert success, "删除应该成功"
    assert len(manager) == 1, "应该剩余 1 个地图"

    # 测试8: 持久化验证
    print("\n【测试8】持久化验证")
    print("  创建新的 MapManager 实例...")
    manager2 = MapManager("./data/test_map_registry.json")
    print(f"  加载了 {len(manager2)} 个地图")
    assert len(manager2) == 1, "应该从文件加载 1 个地图"
    assert manager2.exists("warehouse_floor1"), "应该包含 warehouse_floor1"
    assert not manager2.exists("office_map"), "不应该包含已删除的 office_map"

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_map_manager()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
