"""内容生成 Agent 占位。"""
from __future__ import annotations

from typing import Any


def run_content_generation(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行内容生成步骤；占位返回固定产出。"""
    return {"agent": "内容生成", "output": "占位：正文与配图规划", "step_id": step.get("step_id", "s3")}
