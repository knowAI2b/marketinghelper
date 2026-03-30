"""RAG 检索 Agent：获取选题卡数据支持内容生成。

从 xhs_agent API 获取选题卡数据（趋势、热门话题、竞品分析等），
为选题策划和内容生成提供参考数据。

支持：
- 本地缓存（基于产品信息 fingerprint）
- 失败降级（允许跳过直接生成内容）
"""
from __future__ import annotations

import logging
from typing import Any

from xhs_assistant.services.rag import get_rag_client
from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)

# Agent 名称常量
AGENT_RAG_RETRIEVAL = "RAG检索"

logger = logging.getLogger(__name__)


def run_rag_retrieval(step: dict[str, Any], state: dict[str, Any]) -> Any:
    """执行 RAG 检索步骤。

    调用条件：
    - RAG 服务已启用且可用
    - intent_output 中包含产品信息

    Args:
        step: 步骤信息，包含 step_id, description 等
        state: 工作流状态，包含 intent_output, account_context 等

    Returns:
        dict: 包含 agent, output, step_id, 以及 rag_data
    """
    step_id = step.get("step_id", "s0")

    # 检查 RAG 服务是否启用
    if not config.rag.enabled:
        logger.info("RAG 服务未启用，返回空数据")
        return {
            "agent": AGENT_RAG_RETRIEVAL,
            "output": "RAG 服务未启用",
            "step_id": step_id,
            "rag_data": None,
            "skipped": True,
        }

    client = get_rag_client()
    if not client.is_available():
        logger.info("RAG 服务不可用，返回空数据")
        return {
            "agent": AGENT_RAG_RETRIEVAL,
            "output": "RAG 服务不可用",
            "step_id": step_id,
            "rag_data": None,
            "skipped": True,
        }

    # 从 intent_output 提取产品信息
    intent_output = state.get("intent_output", {})
    slots = intent_output.get("slots", {})

    # 获取产品信息
    product = slots.get("product") or slots.get("topic") or _extract_product_from_demand(
        intent_output.get("demand_summary", "")
    )
    category = slots.get("category") or slots.get("industry")
    topic = slots.get("topic")
    campaign = slots.get("campaign")

    if not product:
        logger.info("未找到产品信息，跳过 RAG 检索")
        return {
            "agent": AGENT_RAG_RETRIEVAL,
            "output": "未找到产品信息",
            "step_id": step_id,
            "rag_data": None,
            "skipped": True,
        }

    # 调用 RAG 服务获取选题卡
    logger.info(f"RAG 检索: product={product}, category={category}, topic={topic}")

    try:
        result = client.get_topic_card_for_product(
            product=product,
            category=category,
            topic=topic,
            campaign=campaign,
            use_cache=True,
        )

        if result.is_success() and result.topic_card:
            # 构建输出
            output_parts = []
            tc = result.topic_card

            if tc.trend_summary:
                output_parts.append(f"趋势摘要: {tc.trend_summary}")
            if tc.title_hooks:
                output_parts.append(f"热门标题: {', '.join(tc.title_hooks[:5])}")
            if tc.recommended_tags:
                output_parts.append(f"推荐标签: {', '.join(tc.recommended_tags[:10])}")

            output = "\n".join(output_parts) if output_parts else "选题卡数据已获取"

            return {
                "agent": AGENT_RAG_RETRIEVAL,
                "output": output,
                "step_id": step_id,
                "rag_data": {
                    "job_id": result.job_id,
                    "topic_card": tc.raw_data,
                    "trend_summary": tc.trend_summary,
                    "title_hooks": tc.title_hooks,
                    "recommended_tags": tc.recommended_tags,
                    "faq_top_questions": tc.faq_top_questions,
                    "compliance_risks": tc.compliance_risks,
                },
                "product": product,
                "category": category,
            }

        else:
            # 失败或无数据，返回空结果（允许降级）
            error_msg = result.error or "未获取到选题卡数据"
            logger.warning(f"RAG 检索失败: {error_msg}")
            return {
                "agent": AGENT_RAG_RETRIEVAL,
                "output": f"检索失败: {error_msg}（已降级）",
                "step_id": step_id,
                "rag_data": None,
                "error": error_msg,
                "degraded": True,
            }

    except Exception as e:
        logger.error(f"RAG 检索异常: {e}")
        return {
            "agent": AGENT_RAG_RETRIEVAL,
            "output": f"检索异常: {e}（已降级）",
            "step_id": step_id,
            "rag_data": None,
            "error": str(e),
            "degraded": True,
        }


def _extract_product_from_demand(demand: str) -> str | None:
    """从需求描述中尝试提取产品名称。

    简单的关键词提取，用于当 slots 中没有明确产品信息时。

    Args:
        demand: 用户需求描述

    Returns:
        str | None: 提取的产品名称
    """
    if not demand:
        return None

    # 简单的关键词匹配
    # TODO: 可以用 NLP 或 LLM 进行更精确的提取
    common_products = [
        "咖啡", "奶茶", "护肤品", "化妆品", "服装", "鞋子", "包包",
        "手机", "电脑", "耳机", "手表", "相机", "家电", "家具",
        "食品", "零食", "饮料", "酒", "茶叶", "保健品",
        "旅游", "酒店", "餐厅", "美食",
    ]

    for product in common_products:
        if product in demand:
            return product

    return None


def get_rag_data_from_state(state: dict[str, Any]) -> dict[str, Any] | None:
    """从 state 中获取 RAG 数据（供其他 Agent 使用）。

    Args:
        state: 工作流状态

    Returns:
        dict | None: RAG 数据
    """
    # 从 past_steps 中查找 RAG 检索的结果
    past_steps = state.get("past_steps", [])

    for step, result in reversed(past_steps):
        if isinstance(result, dict) and result.get("agent") == AGENT_RAG_RETRIEVAL:
            rag_data = result.get("rag_data")
            if rag_data:
                return rag_data

    return None


def format_rag_context(rag_data: dict[str, Any], style: str = "default") -> str:
    """格式化 RAG 数据为上下文字符串（供多个 Agent 共用）。

    Args:
        rag_data: RAG 检索数据
        style: 格式风格 ("default" 或 "bracket")

    Returns:
        str: 格式化的 RAG 数据
    """
    if not rag_data:
        return ""

    # 提取数据
    trend_summary = rag_data.get("trend_summary", "")
    title_hooks = rag_data.get("title_hooks", [])
    recommended_tags = rag_data.get("recommended_tags", [])
    faq_questions = rag_data.get("faq_top_questions", [])
    compliance_risks = rag_data.get("compliance_risks", [])

    # 根据风格选择格式
    use_bracket = style == "bracket"
    parts = []

    if trend_summary:
        parts.append(f"【趋势洞察】\n{trend_summary}" if use_bracket else f"趋势洞察：{trend_summary}")

    if title_hooks:
        hooks = "\n".join(f"- {t}" for t in title_hooks[:5])
        parts.append(f"【热门标题参考】\n{hooks}" if use_bracket else f"热门标题参考：\n{hooks}")

    if recommended_tags:
        tags = ', '.join(recommended_tags[:10])
        parts.append(f"【推荐标签】\n{tags}" if use_bracket else f"推荐标签：{tags}")

    if faq_questions:
        questions = "\n".join(f"- {q}" for q in faq_questions[:3])
        parts.append(f"【用户关注问题】\n{questions}" if use_bracket else f"用户关注问题：\n{questions}")

    if compliance_risks:
        risks = "\n".join(f"- {r}" for r in compliance_risks[:3])
        parts.append(f"【合规提醒】\n{risks}" if use_bracket else f"合规提醒：\n{risks}")

    return "\n\n".join(parts) if parts else ""