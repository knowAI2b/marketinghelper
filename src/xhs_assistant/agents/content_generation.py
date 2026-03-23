"""内容生成 Agent：调用 RedNote 服务生成小红书内容。"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from xhs_assistant.services.rednote import RednoteServiceError, get_rednote_client

logger = logging.getLogger(__name__)

# 用于跟踪哪些 session 是新的（需要清空历史）
_new_sessions: set[str] = set()


def run_content_generation(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行内容生成步骤。

    调用条件：
    - RedNote 服务已启用且可用

    Args:
        step: 步骤信息，包含 step_id, description 等
        state: 工作流状态，包含 intent_output, account_context 等

    Returns:
        dict: 包含 agent, output, step_id，以及生成的内容和图片
    """
    client = get_rednote_client()
    step_id = step.get("step_id", "s3")

    # 检查服务是否可用
    if not client.is_available():
        logger.info("RedNote 服务未启用，返回占位输出")
        return {
            "agent": "内容生成",
            "output": "占位：RedNote 服务未启用",
            "step_id": step_id,
            "content": None,
            "images": [],
        }

    # 获取用户需求和上下文
    intent_output = state.get("intent_output", {})
    account_context = state.get("account_context", {})

    # 获取或创建 session_id
    # 优先使用前端传递的 session_id，确保同一对话使用相同的 ChatAgent
    session_id = account_context.get("session_id") or account_context.get("user_id") or str(uuid.uuid4())

    # 判断是否需要清空历史：
    # - 如果是新的 session（前端传递了 is_new_session=True），则清空
    # - 否则保留历史，让 ChatAgent 能够理解上下文
    is_new_session = account_context.get("is_new_session", False)
    clear_history = is_new_session or session_id not in _new_sessions

    if clear_history:
        _new_sessions.add(session_id)
        logger.info(f"新会话开始, session_id={session_id}")
    else:
        logger.info(f"继续会话, session_id={session_id}")

    # 构建提示词：直接使用用户的原始输入
    # RedNote 服务的 ChatAgent 会管理对话历史
    prompt = _build_generation_prompt(step, intent_output, account_context)

    try:
        logger.info(f"调用 RedNote 服务, session_id={session_id}, clear_history={clear_history}")
        result = client.chat(
            session_id=session_id,
            message=prompt,
            clear_history=clear_history,
        )

        return {
            "agent": "内容生成",
            "output": result.response,
            "step_id": step_id,
            "content": result.response,
            "images": result.images,
            "raw_response": result.raw_response,
            "session_id": session_id,
        }

    except RednoteServiceError as e:
        logger.error(f"RedNote 服务调用失败: {e}")
        return {
            "agent": "内容生成",
            "output": f"生成失败: {e}",
            "step_id": step_id,
            "error": str(e),
            "content": None,
            "images": [],
        }


def _build_generation_prompt(
    step: dict[str, Any],
    intent_output: dict[str, Any],
    account_context: dict[str, Any],
) -> str:
    """构建内容生成提示词。

    Args:
        step: 步骤信息
        intent_output: 意图理解输出
        account_context: 账号上下文

    Returns:
        str: 构建好的提示词
    """
    # 直接使用用户的原始需求
    # ChatAgent 会管理对话历史，后续请求会自动关联之前的上下文
    demand = intent_output.get("demand_summary", "")

    # 如果 demand_summary 包含"之前的对话内容"，说明是后续请求
    # 直接使用它，让 ChatAgent 理解上下文
    if demand:
        return demand

    # 否则使用步骤描述
    step_desc = step.get("input_summary", "") or step.get("description", "")
    if step_desc:
        return step_desc

    # 默认请求
    return "请生成一篇小红书笔记内容"
