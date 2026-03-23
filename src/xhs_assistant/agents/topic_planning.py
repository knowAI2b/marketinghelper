"""选题策划 Agent：根据用户需求和账号定位推荐选题。"""
from __future__ import annotations

import logging
from typing import Any

from xhs_assistant.shared.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的小红书选题策划师。

根据用户的需求、行业和目标受众，推荐 3-5 个高潜选题。

## 输出格式
直接输出选题列表，每个选题包含：
- 标题方向（吸引眼球的切入点）
- 内容概要（简要描述内容方向）
- 预期效果（为什么这个选题好）

## 要求
1. 选题要有热度，贴合小红书用户兴趣
2. 标题要有吸引力，避免标题党
3. 内容方向要具体可执行
4. 不要输出任何元标签或占位符"""


def run_topic_planning(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行选题策划步骤。

    Args:
        step: 步骤信息
        state: 工作流状态

    Returns:
        dict: 包含 agent, output, step_id
    """
    step_id = step.get("step_id", "s2")

    # 提取上下文
    intent_output = state.get("intent_output", {})
    account_context = state.get("account_context", {})

    demand = intent_output.get("demand_summary", "")
    slots = intent_output.get("slots", {})
    platform = slots.get("platform", account_context.get("platform", "小红书"))
    industry = slots.get("industry", account_context.get("industry", ""))
    goal = slots.get("goal", account_context.get("goal", ""))

    # 构建用户消息
    user_message = f"""请帮我做选题策划。

平台：{platform}
行业：{industry or "综合"}
目标：{goal or "综合增长"}
需求：{demand}

请推荐 3-5 个适合的选题。"""

    # 调用 LLM
    try:
        output = call_llm(SYSTEM_PROMPT, user_message, temperature=0.8)
    except Exception as e:
        logger.error(f"Topic planning failed: {e}")
        output = f"选题策划生成失败: {e}"

    return {
        "agent": "选题策划",
        "output": output,
        "step_id": step_id,
    }
