"""Plan、Step、Agent 枚举，与 需求分析与Planner技术调研 第六章一致。"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """五类 Agent 与内容评估。"""

    ACCOUNT_STRATEGY = "账号战略"
    TOPIC_PLANNING = "选题策划"
    CONTENT_GENERATION = "内容生成"
    ADS_PLANNING = "投流"
    CONTENT_EVAL = "内容评估与检验"


class Step(BaseModel):
    """单步：step_id, agent, input_summary, depends_on, acceptance_criteria。"""

    step_id: str = Field(description="步骤 ID")
    agent: str = Field(description="负责 Agent 名称")
    input_summary: str = Field(description="输入摘要")
    depends_on: list[str] = Field(default_factory=list, description="依赖的步骤 ID")
    acceptance_criteria: str | None = Field(default=None, description="验收条件")


class Plan(BaseModel):
    """多步计划。"""

    steps: list[Step] = Field(default_factory=list, description="步骤列表")
