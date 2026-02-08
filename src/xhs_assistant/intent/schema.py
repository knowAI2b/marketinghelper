"""意图输出 Schema，与 意图识别与Planner示例.md 示例 JSON 一致。"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# 槽位：键与 Schema 一致，值来自抽取或补全
Slots = dict[str, Any]


class IntentType(str, Enum):
    """意图类型枚举，与五类 Agent 对齐。"""

    MIXED = "mixed"
    CHAINED = "chained"
    TOPIC_PLANNING = "topic_planning"
    CONTENT_GENERATION = "content_generation"
    ADS_PLANNING = "ads_planning"
    ACCOUNT_STRATEGY = "account_strategy"
    CONTENT_EVAL = "content_eval"
    AMBIGUOUS = "ambiguous"


class IntentOutput(BaseModel):
    """意图理解模块输出：demand_summary, intent_type, slots, needs_clarification 等。"""

    demand_summary: str = Field(description="需求摘要")
    intent_type: str = Field(description="意图类型：mixed/chained/topic_planning/ads_planning 等")
    intent_breakdown: list[str] | None = Field(default=None, description="意图拆解列表（已确定的子意图）")
    intent_breakdown_candidates: list[str] | None = Field(
        default=None, description="意图拆解候选列表（歧义时给出可能的子意图集合）"
    )
    slots: dict[str, Any] = Field(default_factory=dict, description="槽位键值")
    needs_clarification: bool = Field(default=False, description="是否需澄清")
    clarification_question: str | None = Field(default=None, description="澄清问句")
    suggested_agents: list[str] = Field(default_factory=list, description="建议调用的 Agent")
    user_can_edit_task_breakdown: bool = Field(default=False, description="是否支持用户修改任务拆解")
    missing_slots: list[str] | None = Field(default=None, description="缺失槽位（缺槽时）")
    ambiguous_intent: str | None = Field(default=None, description="歧义说明（歧义时）")
