"""
地图名称与索引映射管理模块

功能：
- 维护 map_name ↔ pcdmap_index 双向映射
- 自动分配索引（从 1 开始自增）
- JSON 持久化存储
- 地图元数据管理（创建时间、状态、描述）
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class MapManager:
    """地图名称与索引的映射管理器"""

    def __init__(self, storage_path: str | Path = "./data/map_registry.json"):
        """
        初始化地图管理器

        Args:
            storage_path: 映射数据存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 双向映射
        self.name_to_index: Dict[str, int] = {}  # "office_map" -> 1
        self.index_to_name: Dict[int, str] = {}  # 1 -> "office_map"

        # 地图元数据
        self.map_metadata: Dict[str, dict] = {}  # 存储创建时间、描述、状态等

        # 线程锁（保证并发安全）
        self._lock = Lock()

        # 加载已有映射
        self._load_registry()

        logger.info(f"MapManager 已初始化，存储路径: {self.storage_path}")
        logger.info(f"已加载 {len(self.name_to_index)} 个地图映射")

    def _load_registry(self):
        """从文件加载映射关系"""
        if not self.storage_path.exists():
            logger.info("映射文件不存在，将创建新文件")
            self._save_registry()
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name_to_index = data.get("name_to_index", {})
                # 将 index_to_name 的 key 从字符串转换为整数
                self.index_to_name = {int(k): v for k, v in data.get("index_to_name", {}).items()}
                self.map_metadata = data.get("metadata", {})
            logger.info(f"成功加载映射数据: {len(self.name_to_index)} 个地图")
        except Exception as e:
            logger.error(f"加载映射文件失败: {e}")
            logger.warning("将使用空映射")

    def _save_registry(self):
        """保存映射关系到文件"""
        try:
            data = {
                "name_to_index": self.name_to_index,
                "index_to_name": self.index_to_name,
                "metadata": self.map_metadata,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"映射数据已保存到 {self.storage_path}")
        except Exception as e:
            logger.error(f"保存映射文件失败: {e}")
            raise

    def register_map(self, map_name: str, description: str = "") -> int:
        """
        注册新地图，返回分配的索引

        Args:
            map_name: 地图名称（唯一）
            description: 地图描述

        Returns:
            分配的 pcdmap_index

        Raises:
            ValueError: 如果地图名称无效
        """
        with self._lock:
            # 验证地图名称
            if not map_name or not isinstance(map_name, str):
                raise ValueError("地图名称不能为空")

            # 如果已存在，返回现有索引
            if map_name in self.name_to_index:
                existing_index = self.name_to_index[map_name]
                logger.info(f"地图 '{map_name}' 已存在，索引: {existing_index}")
                return existing_index

            # 分配新索引（从1开始自增）
            if self.index_to_name:
                new_index = max(self.index_to_name.keys()) + 1
            else:
                new_index = 1

            # 建立双向映射
            self.name_to_index[map_name] = new_index
            self.index_to_name[new_index] = map_name

            # 保存元数据
            self.map_metadata[map_name] = {
                "index": new_index,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "status": "creating",  # creating, completed, failed, discarded
            }

            # 持久化
            self._save_registry()

            logger.info(f"注册新地图: '{map_name}' -> 索引 {new_index}")
            return new_index

    def get_index(self, map_name: str) -> Optional[int]:
        """
        根据地图名称获取索引

        Args:
            map_name: 地图名称

        Returns:
            pcdmap_index 或 None（如果不存在）
        """
        return self.name_to_index.get(map_name)

    def get_name(self, index: int) -> Optional[str]:
        """
        根据索引获取地图名称

        Args:
            index: pcdmap_index

        Returns:
            地图名称或 None（如果不存在）
        """
        return self.index_to_name.get(index)

    def update_map_status(self, map_name: str, status: str):
        """
        更新地图状态

        Args:
            map_name: 地图名称
            status: 新状态 (creating, completed, failed, discarded)
        """
        with self._lock:
            if map_name not in self.map_metadata:
                logger.warning(f"地图 '{map_name}' 不存在，无法更新状态")
                return

            self.map_metadata[map_name]["status"] = status
            self.map_metadata[map_name]["updated_at"] = datetime.now().isoformat()
            self._save_registry()

            logger.info(f"地图 '{map_name}' 状态更新为: {status}")

    def get_metadata(self, map_name: str) -> Optional[dict]:
        """
        获取地图元数据

        Args:
            map_name: 地图名称

        Returns:
            元数据字典或 None
        """
        return self.map_metadata.get(map_name)

    def list_maps(self) -> List[dict]:
        """
        列出所有地图

        Returns:
            地图列表，每个元素包含名称、索引和元数据
        """
        result = []
        for name in self.name_to_index.keys():
            map_info = {
                "name": name,
                "index": self.name_to_index[name],
            }
            # 添加元数据
            if name in self.map_metadata:
                map_info.update(self.map_metadata[name])
            result.append(map_info)

        # 按创建时间排序
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    def delete_map(self, map_name: str) -> bool:
        """
        删除地图映射

        Args:
            map_name: 地图名称

        Returns:
            是否删除成功
        """
        with self._lock:
            if map_name not in self.name_to_index:
                logger.warning(f"地图 '{map_name}' 不存在，无法删除")
                return False

            # 删除映射
            index = self.name_to_index[map_name]
            del self.name_to_index[map_name]
            del self.index_to_name[index]

            # 删除元数据
            if map_name in self.map_metadata:
                del self.map_metadata[map_name]

            # 持久化
            self._save_registry()

            logger.info(f"已删除地图映射: '{map_name}' (索引 {index})")
            return True

    def exists(self, map_name: str) -> bool:
        """
        检查地图是否存在

        Args:
            map_name: 地图名称

        Returns:
            是否存在
        """
        return map_name in self.name_to_index

    def clear(self):
        """清空所有映射（谨慎使用！）"""
        with self._lock:
            self.name_to_index.clear()
            self.index_to_name.clear()
            self.map_metadata.clear()
            self._save_registry()
            logger.warning("所有地图映射已清空")

    def __len__(self) -> int:
        """返回地图数量"""
        return len(self.name_to_index)

    def __contains__(self, map_name: str) -> bool:
        """支持 'map_name' in manager 语法"""
        return self.exists(map_name)

    def __repr__(self) -> str:
        return f"<MapManager: {len(self)} maps, storage={self.storage_path}>"


# 全局单例（在应用启动时初始化）
_global_map_manager: Optional[MapManager] = None


def get_map_manager(storage_path: Optional[str | Path] = None) -> MapManager:
    """
    获取全局 MapManager 实例

    Args:
        storage_path: 存储路径（仅首次调用时有效）

    Returns:
        MapManager 实例
    """
    global _global_map_manager
    if _global_map_manager is None:
        from config import config

        path = storage_path or config.MAP_STORAGE_PATH
        _global_map_manager = MapManager(path)
    return _global_map_manager


__all__ = ["MapManager", "get_map_manager"]
