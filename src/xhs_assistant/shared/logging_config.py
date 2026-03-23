"""日志配置模块。

提供统一的日志配置：
- 应用日志：logs/app.log（所有模块日志）
- 用户行为日志：logs/user_action.log（用户操作记录）
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 日志目录（项目根目录下的 logs）
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
APP_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
USER_ACTION_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"

# 日志文件路径
APP_LOG_FILE = LOG_DIR / "app.log"
USER_ACTION_LOG_FILE = LOG_DIR / "user_action.log"

# 是否已初始化
_initialized = False


def setup_logging(
    app_level: str = "INFO",
    console_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """配置应用日志。

    Args:
        app_level: 应用日志级别（DEBUG/INFO/WARNING/ERROR）
        console_level: 控制台日志级别
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
    """
    global _initialized
    if _initialized:
        return

    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置为最低级别，由 handler 控制实际输出

    # 清除已有的 handler
    root_logger.handlers.clear()

    # 1. 应用日志文件 handler
    app_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    app_handler.setLevel(getattr(logging, app_level.upper(), logging.INFO))
    app_handler.setFormatter(logging.Formatter(APP_LOG_FORMAT))
    root_logger.addHandler(app_handler)

    # 2. 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console_handler.setFormatter(logging.Formatter(APP_LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # 3. 降低第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _initialized = True

    logging.info(f"日志系统初始化完成，日志目录: {LOG_DIR}")


def get_user_action_logger() -> logging.Logger:
    """获取用户行为日志记录器。

    Returns:
        Logger: 专门记录用户行为的日志记录器
    """
    logger = logging.getLogger("user_action")

    # 如果已经有 handler，直接返回
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False  # 不传播到根日志

    # 用户行为日志文件 handler
    handler = RotatingFileHandler(
        USER_ACTION_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(USER_ACTION_FORMAT))
    logger.addHandler(handler)

    return logger


# 全局用户行为日志记录器
_user_action_logger: logging.Logger | None = None


def log_user_action(
    action: str,
    user_id: str | None = None,
    session_id: str | None = None,
    details: dict | None = None,
) -> None:
    """记录用户行为日志。

    Args:
        action: 行为类型（如 "login", "register", "create_content", "request_intent"）
        user_id: 用户ID
        session_id: 会话ID
        details: 详细信息
    """
    global _user_action_logger

    if _user_action_logger is None:
        _user_action_logger = get_user_action_logger()

    # 构建日志消息
    parts = [f"action={action}"]
    if user_id:
        parts.append(f"user_id={user_id}")
    if session_id:
        parts.append(f"session_id={session_id}")
    if details:
        # 将 details 转换为 key=value 格式
        detail_strs = [f"{k}={v}" for k, v in details.items() if v is not None]
        parts.extend(detail_strs)

    message = " | ".join(parts)
    _user_action_logger.info(message)


def log_api_request(
    endpoint: str,
    method: str = "POST",
    user_id: str | None = None,
    session_id: str | None = None,
    request_data: dict | None = None,
    response_status: int | None = None,
    duration_ms: float | None = None,
) -> None:
    """记录 API 请求日志。

    Args:
        endpoint: API 端点
        method: HTTP 方法
        user_id: 用户ID
        session_id: 会话ID
        request_data: 请求数据（会脱敏）
        response_status: 响应状态码
        duration_ms: 请求耗时（毫秒）
    """
    details = {
        "endpoint": endpoint,
        "method": method,
    }
    if response_status:
        details["status"] = response_status
    if duration_ms:
        details["duration_ms"] = f"{duration_ms:.2f}"

    log_user_action(
        action="api_request",
        user_id=user_id,
        session_id=session_id,
        details=details,
    )


def get_log_stats() -> dict:
    """获取日志文件统计信息。

    Returns:
        dict: 日志文件信息
    """
    stats = {
        "log_dir": str(LOG_DIR),
        "files": {},
    }

    for log_file in LOG_DIR.glob("*.log*"):
        try:
            stat = log_file.stat()
            stats["files"][log_file.name] = {
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception:
            pass

    return stats