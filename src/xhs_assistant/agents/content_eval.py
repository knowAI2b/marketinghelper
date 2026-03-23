"""内容评估与检验 Agent：评估生成内容的质量并给出改进建议。"""
from __future__ import annotations

import logging
from typing import Any

from xhs_assistant.shared.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的小红书内容评估师。

根据内容质量标准，评估已生成的内容，并给出改进建议。

## 评估维度
1. 标题吸引力（10分）
2. 内容结构（10分）
3. 语言风格（10分）
4. 爆款潜力（10分）
5. 平台适配度（10分）

## 输出格式
直接输出评估结果：

**总分：XX/50**

**各维度评分：**
- 标题吸引力：X/10
- 内容结构：X/10
- 语言风格：X/10
- 爆款潜力：X/10
- 平台适配度：X/10

**优点：**
- ...

**改进建议：**
- ...

## 要求
1. 评分要客观公正
2. 建议要具体可执行
3. 不要输出任何元标签或占位符"""


def run_content_eval(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行内容评估与检验步骤。

    Args:
        step: 步骤信息
        state: 工作流状态

    Returns:
        dict: 包含 agent, output, step_id
    """
    step_id = step.get("step_id", "s5")

    # 从 past_steps 中提取已生成的内容
    past_steps = state.get("past_steps", [])
    generated_content = ""
    for past_step in past_steps:
        _, result = past_step
        if isinstance(result, dict):
            output = result.get("output", "") or result.get("content", "")
            if output:
                generated_content = output
                break

    if not generated_content:
        return {
            "agent": "内容评估与检验",
            "output": "未找到待评估的内容",
            "step_id": step_id,
        }

    # 提取上下文
    intent_output = state.get("intent_output", {})
    slots = intent_output.get("slots", {})
    goal = slots.get("goal", "综合增长")

    # 构建用户消息
    user_message = f"""请评估以下小红书内容：

目标：{goal}

---内容开始---
{generated_content}
---内容结束---

请给出评分和改进建议。"""

    # 调用 LLM
    try:
        output = call_llm(SYSTEM_PROMPT, user_message, temperature=0.5)
    except Exception as e:
        logger.error(f"Content eval failed: {e}")
        output = f"内容评估失败: {e}"

    return {
        "agent": "内容评估与检验",
        "output": output,
        "step_id": step_id,
    }
