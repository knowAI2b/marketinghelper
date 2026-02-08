"""WorkspaceState：LangGraph 工作流状态，与调研第六章数据流一致。"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

# 占位：Plan / Step 在 planner.schema 定义，IntentOutput 在 intent.schema
# 此处仅类型前向引用，运行时由 graph 注入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xhs_assistant.intent.schema import IntentOutput
    from xhs_assistant.planner.schema import Plan, Step


class WorkspaceState(TypedDict, total=False):
    """LangGraph 状态：input, plan, past_steps, response, account_context。"""

    # 用户原始输入
    user_input: str
    # 意图理解输出（意图后写入）
    intent_output: dict[str, Any]
    # 规划产出
    plan: dict[str, Any]
    # 已执行步骤：(step, result) 列表，reducer 为 add
    past_steps: Annotated[list[tuple[dict[str, Any], Any]], operator.add]
    # 最终响应（replan 决定结束时写入）
    response: str
    # 账号上下文（人设、阶段、历史摘要等）
    account_context: dict[str, Any]
