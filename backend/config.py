"""
配置管理模块

从环境变量和 .env 文件加载配置
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """应用配置类"""

    # ============ 运行模式 ============
    SIMULATOR_MODE: bool = os.getenv("SIMULATOR_MODE", "true").lower() == "true"

    # ============ 网络配置 ============
    NETWORK_INTERFACE: Optional[str] = os.getenv("NETWORK_INTERFACE") or None

    # ============ 数据存储 ============
    MAP_STORAGE_PATH: Path = Path(os.getenv("MAP_STORAGE_PATH", "./data/map_registry.json"))
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # ============ 日志配置 ============
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: Path = Path(os.getenv("LOG_FILE", "./logs/backend.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # ============ 服务配置 ============
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ============ CORS 配置 ============
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    ]

    # ============ WebSocket 配置 ============
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))

    # ============ 命令配置 ============
    COMMAND_TIMEOUT: int = int(os.getenv("COMMAND_TIMEOUT", "5"))
    COMMAND_INDEX_START: int = 1
    COMMAND_INDEX_END: int = 10000

    # ============ Odometry 配置 ============
    ODOMETRY_PUBLISH_RATE: int = int(os.getenv("ODOMETRY_PUBLISH_RATE", "10"))

    # ============ Unitree SDK Topics ============
    TOPIC_QT_COMMAND: str = "rt/qt_command"
    TOPIC_QT_NOTICE: str = "rt/qt_notice"
    TOPIC_ODOM: str = "rt/lio_sam_ros2/mapping/re_location_odometry"
    TOPIC_ADD_NODE: str = "rt/qt_add_node"
    TOPIC_ADD_EDGE: str = "rt/qt_add_edge"
    TOPIC_ALL_NODE: str = "rt/all_node"
    TOPIC_ALL_EDGE: str = "rt/all_edge"
    TOPIC_QUERY_RESULT_NODE: str = "rt/query_result_node"
    TOPIC_QUERY_RESULT_EDGE: str = "rt/query_result_edge"

    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.MAP_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def print_config(cls):
        """打印当前配置（用于调试）"""
        print("=" * 60)
        print("Unitree B2 SLAM Backend Configuration")
        print("=" * 60)
        print(f"运行模式: {'仿真模式' if cls.SIMULATOR_MODE else '真实模式'}")
        if not cls.SIMULATOR_MODE:
            print(f"网络接口: {cls.NETWORK_INTERFACE or '默认'}")
        print(f"服务地址: {cls.HOST}:{cls.PORT}")
        print(f"日志级别: {cls.LOG_LEVEL}")
        print(f"日志文件: {cls.LOG_FILE}")
        print(f"地图存储: {cls.MAP_STORAGE_PATH}")
        print(f"CORS 源: {', '.join(cls.CORS_ORIGINS)}")
        print("=" * 60)


# 创建全局配置实例
config = Config()

# 确保目录存在
config.ensure_directories()


# 导出常用配置
__all__ = ["config", "Config"]
