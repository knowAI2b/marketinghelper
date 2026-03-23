"""Native Backend: 基于 LangGraph 的现有实现封装。

直接使用原有的意图识别、规划、执行逻辑，不通过 BackendManager，
避免循环依赖。

可以作为纯本地、无外部依赖的后端使用。
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from xhs_assistant.backends.base import (
    AgentBackend,
    ClarificationOutputData,
    ExecutionOutputData,
    IntentOutputData,
    PlanOutputData,
)
from xhs_assistant.intent.schema import IntentOutput, IntentType

logger = logging.getLogger(__name__)


# 每种意图的「推荐必填槽位」，用于缺槽检测与澄清。
REQUIRED_SLOTS_BY_INTENT: Dict[str, List[str]] = {
    IntentType.TOPIC_PLANNING.value: ["platform", "industry", "goal"],
    IntentType.CONTENT_GENERATION.value: ["platform", "industry", "content_form"],
    IntentType.ADS_PLANNING.value: ["platform", "reference", "budget", "targeting"],
    IntentType.ACCOUNT_STRATEGY.value: ["platform", "industry", "goal", "account_stage"],
}


class NativeBackend(AgentBackend):
    """Native Backend: 纯本地实现，不依赖外部 Agent 框架。

    功能：
    - 意图理解: 使用规则匹配（可启用 LLM）
    - 任务规划: 根据 suggested_agents 生成步骤
    - 步骤执行: 调用注册的 Agent 函数
    - 需求澄清: 基于缺失槽位生成问句

    特点：
    - 无循环依赖
    - 可离线运行
    - 支持可选 LLM 增强
    """

    def __init__(self) -> None:
        """初始化 Native Backend。"""
        self._agent_registry: dict[str, Any] | None = None
        self._llm_chain = None

        # 检查是否启用 LLM
        use_llm = os.getenv("XHS_ASSISTANT_USE_LLM_INTENT", "").lower() in {"1", "true", "yes"}
        if use_llm:
            self._init_llm_chain()

        logger.info(f"NativeBackend initialized (use_llm={use_llm})")

    def _init_llm_chain(self) -> None:
        """初始化 LLM 链（可选）。"""
        try:
            from langchain_core.output_parsers import PydanticOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            parser = PydanticOutputParser(pydantic_object=IntentOutput)
            model_name = os.getenv("XHS_ASSISTANT_INTENT_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(model=model_name, temperature=0)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个为小红书营销助手做需求分析与意图识别的专家。"
                          f"请根据用户输入输出 JSON：{parser.get_format_instructions()}"),
                ("user", "用户输入：{user_input}\n\n账号上下文：{account_context}"),
            ])
            self._llm_chain = prompt | llm | parser
            logger.info(f"LLM chain initialized with model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM chain: {e}")
            self._llm_chain = None

    def _get_agent_registry(self) -> dict[str, Any]:
        """延迟加载 Agent Registry。"""
        if self._agent_registry is None:
            from xhs_assistant.agents.registry import AGENT_REGISTRY
            self._agent_registry = AGENT_REGISTRY
        return self._agent_registry

    # ========================================================================
    # AgentBackend 接口实现
    # ========================================================================

    async def understand_intent(
        self,
        user_input: str,
        account_context: dict[str, Any],
    ) -> IntentOutputData:
        """理解用户意图。"""
        text = (user_input or "").strip()

        # 空输入
        if not text:
            return IntentOutputData(
                demand_summary="用户没有提供任何有效输入。",
                intent_type=IntentType.AMBIGUOUS.value,
                slots={},
                needs_clarification=True,
                clarification_question="请简单描述一下您的需求。",
                missing_slots=["demand"],
            )

        # 尝试 LLM
        if self._llm_chain:
            try:
                result: IntentOutput = self._llm_chain.invoke({
                    "user_input": text,
                    "account_context": account_context,
                })
                return self._fill_slots(
                    IntentOutputData(
                        demand_summary=result.demand_summary,
                        intent_type=result.intent_type,
                        intent_breakdown=result.intent_breakdown,
                        slots=result.slots,
                        needs_clarification=result.needs_clarification,
                        clarification_question=result.clarification_question,
                        suggested_agents=result.suggested_agents,
                        missing_slots=result.missing_slots,
                    ),
                    account_context
                )
            except Exception as e:
                logger.warning(f"LLM intent failed: {e}")

        # 规则占位
        return self._rule_based_intent(text, account_context)

    async def plan_tasks(
        self,
        intent_output: dict[str, Any],
        account_context: dict[str, Any],
    ) -> PlanOutputData:
        """规划任务步骤。"""
        suggested = intent_output.get("suggested_agents") or ["选题策划", "内容生成", "内容评估与检验"]
        steps = [
            {
                "step_id": f"s{i+1}",
                "agent": agent,
                "input_summary": f"执行 {agent}",
                "depends_on": [f"s{i}"] if i > 0 else [],
                "acceptance_criteria": "通过",
            }
            for i, agent in enumerate(suggested)
        ]
        return PlanOutputData(
            steps=steps,
            reasoning=f"根据意图类型 {intent_output.get('intent_type')} 生成 {len(steps)} 个步骤",
        )

    async def execute_step(
        self,
        step: dict[str, Any],
        state: dict[str, Any],
    ) -> ExecutionOutputData:
        """执行单个步骤。"""
        step_id = step.get("step_id", "unknown")
        agent_name = step.get("agent", "")

        try:
            registry = self._get_agent_registry()
            fn = registry.get(agent_name)

            if fn is None:
                return ExecutionOutputData(
                    success=False,
                    output=None,
                    error=f"Unknown agent: {agent_name}",
                    step_id=step_id,
                )

            result = fn(step, state)
            success = "error" not in result if isinstance(result, dict) else True

            return ExecutionOutputData(
                success=success,
                output=result,
                error=result.get("error") if isinstance(result, dict) else None,
                step_id=step_id,
            )

        except Exception as e:
            logger.error(f"Execute step failed: {e}")
            return ExecutionOutputData(
                success=False,
                output=None,
                error=str(e),
                step_id=step_id,
            )

    async def clarify(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> ClarificationOutputData:
        """需求澄清对话。"""
        missing_slots = context.get("missing_slots", [])

        if context.get("clarification_question"):
            return ClarificationOutputData(
                question=context["clarification_question"],
                options=None,
                context_updated=None,
            )

        slot_cn = {
            "industry": "行业（例如美妆、美食、装修）",
            "goal": "目标（例如涨粉、种草、转化）",
            "content_form": "内容形式（图文、视频等）",
            "account_stage": "账号阶段（起号、冷启动、放量、变现）",
        }

        if missing_slots:
            readable = "、".join(slot_cn.get(s, s) for s in missing_slots)
            question = f"为了更好地帮助您，还需要补充一下这些信息：{readable}。请简单说明一下。"
        else:
            question = "请问还有什么需要补充的吗？"

        return ClarificationOutputData(
            question=question,
            options=None,
            context_updated=None,
        )

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _rule_based_intent(
        self,
        text: str,
        account_context: dict[str, Any],
    ) -> IntentOutputData:
        """规则占位意图识别。"""
        return self._fill_slots(
            IntentOutputData(
                demand_summary=text,
                intent_type=IntentType.CHAINED.value,
                intent_breakdown=["topic_planning", "content_generation"],
                slots={"raw_input": text},
                needs_clarification=False,
                suggested_agents=["选题策划", "内容生成", "内容评估与检验"],
            ),
            account_context
        )

    def _fill_slots(
        self,
        intent: IntentOutputData,
        account_context: Dict[str, Any],
    ) -> IntentOutputData:
        """槽位补全。"""
        slots = dict(intent.slots or {})

        # 从 account_context 中的 slots 字段合并（前端传递的已收集槽位）
        context_slots = account_context.get("slots", {})
        if isinstance(context_slots, dict):
            for key, value in context_slots.items():
                if value and key not in slots:
                    slots[key] = value

        # 从 account_context 顶层补充
        for key in ["platform", "industry", "brand", "account_stage", "goal", "topic", "content_form"]:
            if key not in slots and key in account_context:
                slots[key] = account_context[key]

        # content_form 默认值
        if not slots.get("content_form"):
            slots["content_form"] = "图文"

        # 检查必填槽位（排除 content_form，因为有默认值）
        required = REQUIRED_SLOTS_BY_INTENT.get(intent.intent_type, [])
        required_to_check = [name for name in required if name != "content_form"]
        missing = [name for name in required_to_check if not slots.get(name)]

        # 如果已有 platform，不再强制要求其他槽位
        if slots.get("platform"):
            needs_clarification = False
            missing = []
        else:
            needs_clarification = intent.needs_clarification or bool(missing)

        clarification_question = intent.clarification_question

        if missing and not clarification_question:
            clarification_question = self._build_clarification(intent.intent_type, missing)

        return IntentOutputData(
            demand_summary=intent.demand_summary,
            intent_type=intent.intent_type,
            intent_breakdown=intent.intent_breakdown,
            slots=slots,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            missing_slots=missing or intent.missing_slots,
            suggested_agents=intent.suggested_agents,
        )

    def _build_clarification(self, intent_type: str, missing: List[str]) -> str:
        """构建澄清问句。"""
        if not missing:
            return ""

        slot_cn = {
            "platform": "投放平台（如小红书、微信、抖音、朋友圈）",
            "industry": "行业（例如美妆、美食、装修）",
            "goal": "目标（例如涨粉、种草、转化）",
            "content_form": "内容形式（图文、视频等）",
            "account_stage": "账号阶段（起号、冷启动、放量、变现）",
        }

        readable = "、".join(slot_cn.get(s, s) for s in missing)
        action_map = {
            "topic_planning": "做选题策划",
            "content_generation": "生成内容",
            "ads_planning": "做投流规划",
            "account_strategy": "制定账号战略",
        }
        action = action_map.get(intent_type, "完成这次需求")
        return f"为了更好地帮您{action}，还需要补充一下这些信息：{readable}。请简单说明一下。"

    @property
    def backend_name(self) -> str:
        """后端名称。"""
        return "native"