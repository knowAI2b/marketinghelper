"""账号战略 Agent 占位。"""
from __future__ import annotations

from typing import Any


def run_account_strategy(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行账号战略步骤；占位返回固定产出。"""
    return {"agent": "账号战略", "output": "占位：账号定位与人设建议", "step_id": step.get("step_id", "s1")}
