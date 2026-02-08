"""选题策划 Agent 占位。"""
from __future__ import annotations

from typing import Any


def run_topic_planning(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行选题策划步骤；占位返回固定产出。"""
    return {"agent": "选题策划", "output": "占位：选题列表与执行建议", "step_id": step.get("step_id", "s2")}
