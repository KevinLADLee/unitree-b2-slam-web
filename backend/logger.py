"""
日志系统配置

提供统一的日志配置和格式化
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: str = "INFO",
    log_file: Path = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    配置应用日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量

    Returns:
        配置好的 logger
    """
    # 创建 logger
    logger = logging.getLogger("unitree_slam")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler（如果指定了日志文件）
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"日志文件已配置: {log_file}")

    # 防止日志传播到根 logger
    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，如果为 None 则返回根 logger

    Returns:
        logger 实例
    """
    if name:
        return logging.getLogger(f"unitree_slam.{name}")
    return logging.getLogger("unitree_slam")


# 初始化日志系统（在导入时执行）
def init_logging():
    """初始化日志系统（从配置加载）"""
    from config import config

    setup_logging(
        log_level=config.LOG_LEVEL,
        log_file=config.LOG_FILE if hasattr(config, "LOG_FILE") else None,
        max_bytes=config.LOG_MAX_BYTES if hasattr(config, "LOG_MAX_BYTES") else 10 * 1024 * 1024,
        backup_count=config.LOG_BACKUP_COUNT if hasattr(config, "LOG_BACKUP_COUNT") else 5,
    )


__all__ = ["setup_logging", "get_logger", "init_logging"]
