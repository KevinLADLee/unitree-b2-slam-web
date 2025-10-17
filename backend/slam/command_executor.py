"""
命令执行器

管理命令索引、状态追踪和超时处理
"""

import time
import asyncio
from typing import Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from threading import Lock

from config import config
from logger import get_logger
from slam.message_types import CommandFeedback, QtNotice

logger = get_logger("command_executor")


class CommandStatus(Enum):
    """命令执行状态"""

    PENDING = "pending"      # 等待执行
    SENT = "sent"           # 已发送
    SUCCESS = "success"     # 执行成功
    FAILED = "failed"       # 执行失败
    TIMEOUT = "timeout"     # 执行超时


@dataclass
class CommandRecord:
    """命令记录"""

    index: int                          # 命令索引
    command_type: str                   # 命令类型
    status: CommandStatus               # 命令状态
    sent_time: float                    # 发送时间
    response_time: Optional[float] = None   # 响应时间
    feedback: Optional[int] = None      # 反馈值
    notice: Optional[str] = None        # 通知消息
    error: Optional[str] = None         # 错误信息


class CommandExecutor:
    """命令执行器"""

    def __init__(
        self,
        start_index: int = 1,
        end_index: int = 10000,
        timeout: int = None,
    ):
        """
        初始化命令执行器

        Args:
            start_index: 起始索引
            end_index: 结束索引
            timeout: 命令超时时间（秒），None 使用配置值
        """
        self.start_index = start_index
        self.end_index = end_index
        self.timeout = timeout or config.COMMAND_TIMEOUT

        # 当前索引
        self._current_index = start_index
        self._index_lock = Lock()

        # 命令记录
        self._commands: Dict[int, CommandRecord] = {}
        self._commands_lock = Lock()

        # 回调函数
        self._on_success: Optional[Callable] = None
        self._on_failure: Optional[Callable] = None

        logger.info(
            f"CommandExecutor 初始化: "
            f"index_range=[{start_index}, {end_index}], "
            f"timeout={self.timeout}s"
        )

    def get_next_index(self) -> int:
        """
        获取下一个命令索引

        Returns:
            命令索引

        Raises:
            RuntimeError: 如果索引超出范围
        """
        with self._index_lock:
            if self._current_index > self.end_index:
                # 重置索引
                logger.warning(f"命令索引超出范围，重置为 {self.start_index}")
                self._current_index = self.start_index

            index = self._current_index
            self._current_index += 1

            logger.debug(f"分配命令索引: {index}")
            return index

    def register_command(self, index: int, command_type: str):
        """
        注册命令

        Args:
            index: 命令索引
            command_type: 命令类型
        """
        with self._commands_lock:
            record = CommandRecord(
                index=index,
                command_type=command_type,
                status=CommandStatus.SENT,
                sent_time=time.time(),
            )
            self._commands[index] = record

            logger.debug(f"注册命令: index={index}, type={command_type}")

    def handle_feedback(self, qt_notice: QtNotice):
        """
        处理命令反馈

        Args:
            qt_notice: Qt Notice 消息
        """
        index = qt_notice.index

        with self._commands_lock:
            if index not in self._commands:
                logger.warning(f"收到未知命令的反馈: index={index}")
                return

            record = self._commands[index]
            record.response_time = time.time()
            record.feedback = qt_notice.feedback
            record.notice = qt_notice.notice

            # 更新状态
            if qt_notice.feedback == CommandFeedback.SUCCESS:
                record.status = CommandStatus.SUCCESS
                logger.info(
                    f"命令执行成功: index={index}, "
                    f"type={record.command_type}, "
                    f"time={record.response_time - record.sent_time:.3f}s"
                )

                # 触发成功回调
                if self._on_success:
                    try:
                        self._on_success(record)
                    except Exception as e:
                        logger.error(f"成功回调执行失败: {e}")

            elif qt_notice.feedback in [CommandFeedback.FAILED, CommandFeedback.ERROR]:
                record.status = CommandStatus.FAILED
                record.error = qt_notice.notice
                logger.error(
                    f"命令执行失败: index={index}, "
                    f"type={record.command_type}, "
                    f"error={qt_notice.notice}"
                )

                # 触发失败回调
                if self._on_failure:
                    try:
                        self._on_failure(record)
                    except Exception as e:
                        logger.error(f"失败回调执行失败: {e}")

            elif qt_notice.feedback == CommandFeedback.WAITING:
                logger.debug(f"命令等待中: index={index}")

    def check_timeout(self):
        """检查超时的命令"""
        current_time = time.time()

        with self._commands_lock:
            for index, record in self._commands.items():
                if record.status == CommandStatus.SENT:
                    elapsed = current_time - record.sent_time
                    if elapsed > self.timeout:
                        record.status = CommandStatus.TIMEOUT
                        record.error = f"命令超时 ({elapsed:.1f}s)"
                        logger.warning(
                            f"命令超时: index={index}, "
                            f"type={record.command_type}, "
                            f"elapsed={elapsed:.1f}s"
                        )

                        # 触发失败回调
                        if self._on_failure:
                            try:
                                self._on_failure(record)
                            except Exception as e:
                                logger.error(f"失败回调执行失败: {e}")

    async def wait_for_command(
        self, index: int, timeout: Optional[float] = None
    ) -> CommandRecord:
        """
        等待命令完成

        Args:
            index: 命令索引
            timeout: 超时时间（秒），None 使用默认值

        Returns:
            命令记录

        Raises:
            TimeoutError: 如果超时
            KeyError: 如果命令不存在
        """
        timeout = timeout or self.timeout
        start_time = time.time()

        while True:
            with self._commands_lock:
                if index not in self._commands:
                    raise KeyError(f"命令不存在: index={index}")

                record = self._commands[index]

                if record.status in [
                    CommandStatus.SUCCESS,
                    CommandStatus.FAILED,
                    CommandStatus.TIMEOUT,
                ]:
                    return record

            # 检查超时
            if time.time() - start_time > timeout:
                with self._commands_lock:
                    record = self._commands[index]
                    record.status = CommandStatus.TIMEOUT
                    record.error = f"等待超时 ({timeout}s)"
                raise TimeoutError(f"等待命令完成超时: index={index}")

            # 短暂休眠
            await asyncio.sleep(0.1)

    def get_command(self, index: int) -> Optional[CommandRecord]:
        """
        获取命令记录

        Args:
            index: 命令索引

        Returns:
            命令记录，如果不存在返回 None
        """
        with self._commands_lock:
            return self._commands.get(index)

    def get_pending_commands(self) -> list[CommandRecord]:
        """获取所有待处理的命令"""
        with self._commands_lock:
            return [
                record
                for record in self._commands.values()
                if record.status == CommandStatus.SENT
            ]

    def clear_old_commands(self, max_age: float = 300):
        """
        清理旧的命令记录

        Args:
            max_age: 最大保留时间（秒）
        """
        current_time = time.time()
        removed_count = 0

        with self._commands_lock:
            indices_to_remove = []
            for index, record in self._commands.items():
                # 只清理已完成或失败的命令
                if record.status in [
                    CommandStatus.SUCCESS,
                    CommandStatus.FAILED,
                    CommandStatus.TIMEOUT,
                ]:
                    age = current_time - record.sent_time
                    if age > max_age:
                        indices_to_remove.append(index)

            for index in indices_to_remove:
                del self._commands[index]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 条旧命令记录")

    def set_success_callback(self, callback: Callable[[CommandRecord], None]):
        """设置成功回调"""
        self._on_success = callback

    def set_failure_callback(self, callback: Callable[[CommandRecord], None]):
        """设置失败回调"""
        self._on_failure = callback

    def get_statistics(self) -> dict:
        """获取命令执行统计"""
        with self._commands_lock:
            stats = {
                "total": len(self._commands),
                "pending": 0,
                "sent": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
            }

            for record in self._commands.values():
                if record.status == CommandStatus.PENDING:
                    stats["pending"] += 1
                elif record.status == CommandStatus.SENT:
                    stats["sent"] += 1
                elif record.status == CommandStatus.SUCCESS:
                    stats["success"] += 1
                elif record.status == CommandStatus.FAILED:
                    stats["failed"] += 1
                elif record.status == CommandStatus.TIMEOUT:
                    stats["timeout"] += 1

            return stats

    def reset(self):
        """重置执行器"""
        with self._index_lock:
            self._current_index = self.start_index

        with self._commands_lock:
            self._commands.clear()

        logger.info("CommandExecutor 已重置")


__all__ = [
    "CommandExecutor",
    "CommandStatus",
    "CommandRecord",
]
