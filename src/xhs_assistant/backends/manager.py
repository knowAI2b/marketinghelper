"""Backend Manager: Agent 后端管理器。

根据配置选择并缓存 AgentBackend 实例，支持：
- 全局后端类型配置
- 模块级别后端覆盖
- 单例模式管理后端实例
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xhs_assistant.backends.base import AgentBackend, BackendType
from xhs_assistant.shared.config import config

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BackendManager:
    """Agent 后端管理器。

    功能：
    - 根据配置选择后端实现（native/nanobot/nanoclaw）
    - 支持模块级别的后端覆盖（intent/planner/executor）
    - 单例模式，避免重复初始化

    使用示例：
        # 获取默认后端
        backend = BackendManager.get_backend()

        # 获取特定模块的后端
        intent_backend = BackendManager.get_intent_backend()
        planner_backend = BackendManager.get_planner_backend()
        executor_backend = BackendManager.get_executor_backend()
    """

    # 后端实例缓存
    _instances: dict[str, AgentBackend] = {}

    @classmethod
    def get_backend(cls, backend_type: str | None = None) -> AgentBackend:
        """获取指定类型的后端实例（单例）。

        Args:
            backend_type: 后端类型，None 时使用配置中的默认类型

        Returns:
            AgentBackend: 对应类型的后端实例

        Raises:
            ValueError: 未知的后端类型
            NotImplementedError: 后端尚未实现
        """
        # 从配置获取默认类型
        if backend_type is None:
            backend_type = config.agent_backend.backend_type

        # 验证后端类型
        if not BackendType.is_valid(backend_type):
            raise ValueError(
                f"Unknown backend type: {backend_type}. "
                f"Valid types: {BackendType.all()}"
            )

        # 检查缓存
        if backend_type in cls._instances:
            return cls._instances[backend_type]

        # 创建新实例
        logger.info(f"Creating backend instance: {backend_type}")
        backend = cls._create_backend(backend_type)
        cls._instances[backend_type] = backend

        return backend

    @classmethod
    def get_intent_backend(cls) -> AgentBackend:
        """获取意图识别后端。

        支持通过 XHS_INTENT_BACKEND 环境变量覆盖全局配置。

        Returns:
            AgentBackend: 意图识别后端实例
        """
        backend_type = config.agent_backend.get_effective_backend("intent")
        logger.debug(f"Intent backend: {backend_type}")
        return cls.get_backend(backend_type)

    @classmethod
    def get_planner_backend(cls) -> AgentBackend:
        """获取任务规划后端。

        支持通过 XHS_PLANNER_BACKEND 环境变量覆盖全局配置。

        Returns:
            AgentBackend: 任务规划后端实例
        """
        backend_type = config.agent_backend.get_effective_backend("planner")
        logger.debug(f"Planner backend: {backend_type}")
        return cls.get_backend(backend_type)

    @classmethod
    def get_executor_backend(cls) -> AgentBackend:
        """获取步骤执行后端。

        支持通过 XHS_EXECUTOR_BACKEND 环境变量覆盖全局配置。

        Returns:
            AgentBackend: 步骤执行后端实例
        """
        backend_type = config.agent_backend.get_effective_backend("executor")
        logger.debug(f"Executor backend: {backend_type}")
        return cls.get_backend(backend_type)

    @classmethod
    def _create_backend(cls, backend_type: str) -> AgentBackend:
        """创建指定类型的后端实例。

        Args:
            backend_type: 后端类型

        Returns:
            AgentBackend: 新创建的后端实例

        Raises:
            NotImplementedError: 后端尚未实现
        """
        if backend_type == BackendType.NATIVE:
            from xhs_assistant.backends.native_backend import NativeBackend
            return NativeBackend()

        elif backend_type == BackendType.NANOBOT:
            from xhs_assistant.backends.nanobot_backend import NanobotBackend
            return NanobotBackend()

        elif backend_type == BackendType.NANOCLAW:
            # 后续扩展
            raise NotImplementedError(
                "Nanoclaw backend is not implemented yet. "
                "Please use 'native' or 'nanobot' for now."
            )

        else:
            # 理论上不会到达这里，因为前面已经验证过类型
            raise ValueError(f"Unknown backend type: {backend_type}")

    @classmethod
    def clear_cache(cls) -> None:
        """清空后端实例缓存。

        用于测试或需要重新初始化后端的场景。
        """
        logger.info("Clearing backend cache")
        cls._instances.clear()

    @classmethod
    def get_active_backends(cls) -> list[str]:
        """获取当前已初始化的后端列表。

        Returns:
            list[str]: 已初始化的后端类型列表
        """
        return list(cls._instances.keys())

    @classmethod
    def health_check(cls) -> dict[str, bool]:
        """检查所有已初始化后端的健康状态。

        Returns:
            dict[str, bool]: 后端名称 -> 健康状态
        """
        result = {}
        for backend_type, backend in cls._instances.items():
            try:
                import asyncio
                healthy = asyncio.run(backend.health_check())
                result[backend_type] = healthy
            except Exception as e:
                logger.warning(f"Health check failed for {backend_type}: {e}")
                result[backend_type] = False
        return result

    @classmethod
    async def close_all(cls) -> None:
        """关闭所有已初始化的后端，释放资源。"""
        logger.info("Closing all backends")
        for backend_type, backend in cls._instances.items():
            try:
                await backend.close()
                logger.debug(f"Closed backend: {backend_type}")
            except Exception as e:
                logger.warning(f"Failed to close backend {backend_type}: {e}")
        cls._instances.clear()


# ============================================================================
# 便捷函数
# ============================================================================

def get_backend() -> AgentBackend:
    """获取默认后端实例的便捷函数。"""
    return BackendManager.get_backend()


def get_intent_backend() -> AgentBackend:
    """获取意图识别后端的便捷函数。"""
    return BackendManager.get_intent_backend()


def get_planner_backend() -> AgentBackend:
    """获取任务规划后端的便捷函数。"""
    return BackendManager.get_planner_backend()


def get_executor_backend() -> AgentBackend:
    """获取步骤执行后端的便捷函数。"""
    return BackendManager.get_executor_backend()