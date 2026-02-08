"""agent 名称 → 可调用实现；执行函数接收 (step, state) 返回该步产出。"""
from __future__ import annotations

from typing import Any, Callable

from xhs_assistant.agents.account_strategy import run_account_strategy
from xhs_assistant.agents.ads_planning import run_ads_planning
from xhs_assistant.agents.content_eval import run_content_eval
from xhs_assistant.agents.content_generation import run_content_generation
from xhs_assistant.agents.topic_planning import run_topic_planning

AgentFn = Callable[[dict[str, Any], dict[str, Any]], Any]

AGENT_REGISTRY: dict[str, AgentFn] = {
    "账号战略": run_account_strategy,
    "选题策划": run_topic_planning,
    "内容生成": run_content_generation,
    "投流": run_ads_planning,
    "内容评估与检验": run_content_eval,
}


def run_agent(agent_name: str, step: dict[str, Any], state: dict[str, Any]) -> Any:
    """根据 agent 名称执行对应步骤。"""
    fn = AGENT_REGISTRY.get(agent_name)
    if fn is None:
        return {"error": f"unknown agent: {agent_name}", "step_id": step.get("step_id")}
    return fn(step, state)
