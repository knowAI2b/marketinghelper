"""Agent 后端模块。

提供统一的 Agent 能力抽象，支持多种后端实现：
- NativeBackend: 基于 LangGraph 的现有实现
- NanobotBackend: 基于 nanobot 框架的实现
- NanoclawBackend: 基于 nanoclaw 的实现（后续扩展）

使用示例：
    from xhs_assistant.backends import BackendManager, get_backend

    # 获取默认后端
    backend = get_backend()

    # 使用后端进行意图理解
    intent = await backend.understand_intent("帮我起个美妆账号", {})

    # 或者使用 BackendManager 获取特定模块的后端
    intent_backend = BackendManager.get_intent_backend()
    planner_backend = BackendManager.get_planner_backend()
"""
from xhs_assistant.backends.base import (
    AgentBackend,
    BackendType,
    ClarificationOutputData,
    ClarificationResult,
    ExecutionOutputData,
    ExecutionResult,
    IntentOutputData,
    IntentResult,
    PlanOutputData,
    PlanResult,
)
from xhs_assistant.backends.manager import (
    BackendManager,
    get_backend,
    get_executor_backend,
    get_intent_backend,
    get_planner_backend,
)
from xhs_assistant.backends.native_backend import NativeBackend
from xhs_assistant.backends.nanobot_backend import NanobotBackend

__all__ = [
    # 抽象基类
    "AgentBackend",
    # 结果协议
    "IntentResult",
    "PlanResult",
    "ExecutionResult",
    "ClarificationResult",
    # 结果数据类
    "IntentOutputData",
    "PlanOutputData",
    "ExecutionOutputData",
    "ClarificationOutputData",
    # 后端类型
    "BackendType",
    # 后端实现
    "NativeBackend",
    "NanobotBackend",
    # 后端管理器
    "BackendManager",
    # 便捷函数
    "get_backend",
    "get_intent_backend",
    "get_planner_backend",
    "get_executor_backend",
]