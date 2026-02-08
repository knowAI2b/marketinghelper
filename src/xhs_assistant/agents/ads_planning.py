"""投流 Agent 占位。"""
from __future__ import annotations

from typing import Any


def run_ads_planning(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行投流步骤；占位返回固定产出。"""
    return {"agent": "投流", "output": "占位：投流策略与候选笔记", "step_id": step.get("step_id", "s4")}
