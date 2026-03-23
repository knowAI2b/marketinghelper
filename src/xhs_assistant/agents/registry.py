"""Agent Registry: agent 名称 → 可调用实现。

支持多种后端：
- native: 直接调用本地 Agent 函数
- nanobot: 通过 BackendManager 调用

执行函数接收 (step, state) 返回该步产出。
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from xhs_assistant.agents.account_strategy import run_account_strategy
from xhs_assistant.agents.ads_planning import run_ads_planning
from xhs_assistant.agents.content_eval import run_content_eval
from xhs_assistant.agents.content_generation import run_content_generation
from xhs_assistant.agents.topic_planning import run_topic_planning
from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


AgentFn = Callable[[dict[str, Any], dict[str, Any]], Any]

# Agent 注册表：名称 → 执行函数
AGENT_REGISTRY: dict[str, AgentFn] = {
    "账号战略": run_account_strategy,
    "选题策划": run_topic_planning,
    "内容生成": run_content_generation,
    "投流": run_ads_planning,
    "内容评估与检验": run_content_eval,
}


def run_agent(agent_name: str, step: dict[str, Any], state: dict[str, Any]) -> Any:
    """根据 agent 名称执行对应步骤（Native 后端）。

    Args:
        agent_name: Agent 名称
        step: 步骤信息
        state: 工作流状态

    Returns:
        Any: 执行结果
    """
    fn = AGENT_REGISTRY.get(agent_name)
    if fn is None:
        logger.warning(f"Unknown agent: {agent_name}")
        return {"error": f"unknown agent: {agent_name}", "step_id": step.get("step_id")}

    try:
        logger.debug(f"Running agent: {agent_name}")
        result = fn(step, state)
        return result
    except Exception as e:
        logger.error(f"Agent {agent_name} failed: {e}")
        return {"error": str(e), "step_id": step.get("step_id"), "agent": agent_name}


def get_available_agents() -> list[str]:
    """获取所有可用的 Agent 名称列表。

    Returns:
        list[str]: Agent 名称列表
    """
    return list(AGENT_REGISTRY.keys())


def get_agent_info(agent_name: str) -> dict[str, Any] | None:
    """获取 Agent 信息。

    Args:
        agent_name: Agent 名称

    Returns:
        dict | None: Agent 信息，不存在返回 None
    """
    if agent_name not in AGENT_REGISTRY:
        return None

    fn = AGENT_REGISTRY[agent_name]
    return {
        "name": agent_name,
        "function": fn.__name__,
        "module": fn.__module__,
        "doc": fn.__doc__ or "",
    }


def register_agent(name: str, fn: AgentFn) -> None:
    """注册新的 Agent。

    Args:
        name: Agent 名称
        fn: 执行函数
    """
    if name in AGENT_REGISTRY:
        logger.warning(f"Overwriting existing agent: {name}")
    AGENT_REGISTRY[name] = fn
    logger.info(f"Registered agent: {name}")


def unregister_agent(name: str) -> bool:
    """注销 Agent。

    Args:
        name: Agent 名称

    Returns:
        bool: 是否成功注销
    """
    if name in AGENT_REGISTRY:
        del AGENT_REGISTRY[name]
        logger.info(f"Unregistered agent: {name}")
        return True
    return False


# ============================================================================
# 后端信息
# ============================================================================

def get_executor_backend_type() -> str:
    """获取执行器后端类型。

    Returns:
        str: 后端类型 (native/nanobot/nanoclaw)
    """
    return config.agent_backend.get_effective_backend("executor")


def get_registry_info() -> dict[str, Any]:
    """获取注册表信息。

    Returns:
        dict: 注册表信息
    """
    return {
        "agents": get_available_agents(),
        "count": len(AGENT_REGISTRY),
        "executor_backend": get_executor_backend_type(),
    }