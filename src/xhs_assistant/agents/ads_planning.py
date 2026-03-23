"""投流 Agent：根据内容和目标制定付费推广策略。"""
from __future__ import annotations

import logging
from typing import Any

from xhs_assistant.shared.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的小红书投流策略师。

根据内容和推广目标，制定付费推广策略。

## 输出格式
直接输出投流策略，包括：

**推荐投流方式：**
- 薯条推广 / 信息流广告 / 蒲公英合作
- 推荐理由

**目标人群定向：**
- 年龄范围
- 性别
- 兴趣标签
- 地域

**预算建议：**
- 测试期预算
- 放量期预算
- 预期 ROI

**投放时机：**
- 最佳发布时间
- 投放时长

## 要求
1. 策略要结合平台特点
2. 预算建议要合理
3. 不要输出任何元标签或占位符"""


def run_ads_planning(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行投流步骤。

    Args:
        step: 步骤信息
        state: 工作流状态

    Returns:
        dict: 包含 agent, output, step_id
    """
    step_id = step.get("step_id", "s4")

    # 从 past_steps 中提取已生成的内容
    past_steps = state.get("past_steps", [])
    generated_content = ""
    for past_step in past_steps:
        _, result = past_step
        if isinstance(result, dict):
            output = result.get("output", "") or result.get("content", "")
            if output:
                generated_content = output[:500]  # 只取前500字
                break

    # 提取上下文
    intent_output = state.get("intent_output", {})
    account_context = state.get("account_context", {})

    slots = intent_output.get("slots", {})
    platform = slots.get("platform", account_context.get("platform", "小红书"))
    industry = slots.get("industry", account_context.get("industry", ""))
    goal = slots.get("goal", account_context.get("goal", ""))

    # 构建用户消息
    user_message = f"""请帮我制定投流策略。

平台：{platform}
行业：{industry or "综合"}
推广目标：{goal or "综合增长"}

待推广内容摘要：
{generated_content or "暂无具体内容"}

请给出投流策略建议。"""

    # 调用 LLM
    try:
        output = call_llm(SYSTEM_PROMPT, user_message, temperature=0.7)
    except Exception as e:
        logger.error(f"Ads planning failed: {e}")
        output = f"投流策略生成失败: {e}"

    return {
        "agent": "投流",
        "output": output,
        "step_id": step_id,
    }
