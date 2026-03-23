"""共享的 LLM 调用工具。

提供统一的 LLM 调用接口，供各 Agent 使用。
"""
from __future__ import annotations

import logging
import os
from typing import Any

from litellm import completion

logger = logging.getLogger(__name__)


def get_llm_config() -> dict[str, Any]:
    """获取 LLM 配置。

    Returns:
        dict: 包含 model, api_key, api_base
    """
    return {
        "model": os.getenv("XHS_NANOBOT_MODEL", "openai/qwen3-coder-plus"),
        "api_key": os.getenv("XHS_NANOBOT_API_KEY", ""),
        "api_base": os.getenv("XHS_NANOBOT_API_BASE", ""),
    }


def call_llm(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """调用 LLM 生成内容。

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        str: LLM 生成的文本
    """
    config = get_llm_config()

    try:
        response = completion(
            model=config["model"],
            api_key=config["api_key"],
            api_base=config["api_base"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"LLM 调用失败: {e}"


def call_llm_json(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """调用 LLM 并解析 JSON 响应。

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        dict: 解析后的 JSON 对象
    """
    import json
    import re

    text = call_llm(system_prompt, user_message, temperature, max_tokens)

    # 尝试提取 JSON
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1).strip()
    else:
        # 尝试匹配 { ... } 块
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            text = brace_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}")
        return {"raw_response": text}