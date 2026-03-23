"""账号战略 Agent：根据用户需求提供账号定位与人设建议。"""
from __future__ import annotations

import logging
from typing import Any

from xhs_assistant.shared.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的小红书账号战略顾问。

根据用户的需求和当前状态，提供账号定位与人设建议。

## 输出格式
直接输出建议内容，包括：
1. 账号定位建议（目标人群、内容方向）
2. 人设塑造要点（风格、语言特色）
3. 内容策略建议（发布频率、内容类型配比）
4. 成长路径规划（起号/冷启动/放量/变现阶段的重点）

## 要求
1. 建议要具体可执行，不要空泛
2. 结合小红书平台特点
3. 不要输出任何元标签或占位符"""


def run_account_strategy(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行账号战略步骤。

    Args:
        step: 步骤信息
        state: 工作流状态

    Returns:
        dict: 包含 agent, output, step_id
    """
    step_id = step.get("step_id", "s1")

    # 提取上下文
    intent_output = state.get("intent_output", {})
    account_context = state.get("account_context", {})

    demand = intent_output.get("demand_summary", "")
    slots = intent_output.get("slots", {})
    platform = slots.get("platform", account_context.get("platform", "小红书"))
    industry = slots.get("industry", account_context.get("industry", ""))
    goal = slots.get("goal", account_context.get("goal", ""))
    account_stage = slots.get("account_stage", account_context.get("account_stage", ""))

    # 构建用户消息
    user_message = f"""请帮我制定账号战略。

平台：{platform}
行业：{industry or "综合"}
目标：{goal or "综合增长"}
账号阶段：{account_stage or "未确定"}
需求：{demand}

请提供账号定位与人设建议。"""

    # 调用 LLM
    try:
        output = call_llm(SYSTEM_PROMPT, user_message, temperature=0.7)
    except Exception as e:
        logger.error(f"Account strategy failed: {e}")
        output = f"账号战略生成失败: {e}"

    return {
        "agent": "账号战略",
        "output": output,
        "step_id": step_id,
    }
