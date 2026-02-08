"""意图识别服务：槽位补全 + 大模型结构化输出 + 规则兜底。

设计目标：
- 支持「槽位补全」：结合用户输入 + 账号上下文 + 必填槽配置，自动补充 slots，并在缺槽时输出澄清信息。
- 支持「大模型请求与解析」：通过 LangChain 的 Pydantic 结构化输出从 LLM 获得 `IntentOutput`。
- 高鲁棒性：任何 LLM 解析失败或环境问题时，均能回退到规则占位实现，保证不崩溃。

后续若接入真实 LLM，只需在配置中打开开关或替换底层 Chat 模型。
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from xhs_assistant.intent.schema import IntentOutput, IntentType


# 每种意图的「推荐必填槽位」，用于缺槽检测与澄清。
REQUIRED_SLOTS_BY_INTENT: Dict[str, List[str]] = {
    IntentType.TOPIC_PLANNING.value: ["industry", "goal"],
    IntentType.CONTENT_GENERATION.value: ["industry", "content_form"],
    IntentType.ADS_PLANNING.value: ["reference", "budget", "targeting"],
    IntentType.ACCOUNT_STRATEGY.value: ["industry", "goal", "account_stage"],
}


class IntentService:
    """意图理解服务。

    - 首选使用大模型按 Pydantic Schema 输出 `IntentOutput`。
    - 然后做槽位补全与缺槽检测（needs_clarification / missing_slots / clarification_question）。
    - 若大模型不可用或解析失败，则使用规则占位逻辑兜底。
    """

    def __init__(self, use_llm: bool | None = None) -> None:
        # 默认从环境变量控制是否启用 LLM；不启用则只用规则占位（便于本地无 Key 时开发）
        if use_llm is None:
            env_flag = os.getenv("XHS_ASSISTANT_USE_LLM_INTENT", "").lower()
            use_llm = env_flag in {"1", "true", "yes"}
        self.use_llm = use_llm

        self._llm = None
        self._prompt = None
        # 使用新版 langchain-core 的初始化方式：需要传入 pydantic_object 字段
        self._parser = PydanticOutputParser(pydantic_object=IntentOutput)

        if self.use_llm:
            # 这里示例使用 OpenAI Chat，后续可按 config 抽象为多厂商
            model_name = os.getenv("XHS_ASSISTANT_INTENT_MODEL", "gpt-4o-mini")
            self._llm = ChatOpenAI(model=model_name, temperature=0)
            self._prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        (
                            "你是一个为小红书营销助手做需求分析与意图识别的专家。"
                            "请根据用户输入和账号上下文，输出一个 JSON，结构必须严格符合下面的说明：\n"
                            f"{self._parser.get_format_instructions()}"
                        ),
                    ),
                    (
                        "user",
                        "用户输入：{user_input}\n\n账号上下文：{account_context}\n\n"
                        "请根据说明输出 IntentOutput JSON，不要添加多余解释。",
                    ),
                ]
            )

    def run(self, user_input: str, account_context: Dict[str, Any] | None = None) -> IntentOutput:
        """解析用户输入，返回结构化意图。

        - 正常：返回 `needs_clarification=False` 且必填槽位尽量齐全。
        - 缺槽/歧义：返回 `needs_clarification=True`、`missing_slots` 与 `clarification_question`。
        - 任何异常：回退到规则占位实现，保证不抛出到上层。
        """
        text = (user_input or "").strip()
        account_context = account_context or {}

        # 空输入直接澄清
        if not text:
            return IntentOutput(
                demand_summary="用户没有提供任何有效输入，需要澄清具体需求。",
                intent_type=IntentType.AMBIGUOUS.value,
                slots={},
                needs_clarification=True,
                clarification_question="请简单描述一下，您想让我在小红书这边帮您做什么？例如：起号、选题策划、写一篇笔记、做投流等。",
                missing_slots=["demand"],
            )

        # 优先尝试 LLM 结构化输出
        if self.use_llm and self._llm and self._prompt:
            try:
                chain = self._prompt | self._llm | self._parser
                intent: IntentOutput = chain.invoke(
                    {"user_input": text, "account_context": account_context}
                )
                return self._fill_slots(intent, account_context)
            except Exception:
                # LLM 失败时降级到规则占位
                pass

        # 规则占位实现（基于文档示例做简化规则），同时也做槽位补全
        intent = self._rule_based_intent(text, account_context)
        return self._fill_slots(intent, account_context)

    # -------- 槽位补全与缺槽检测 --------

    def _fill_slots(self, intent: IntentOutput, account_context: Dict[str, Any]) -> IntentOutput:
        """合并 slots 与账号上下文，并根据意图类型做缺槽检测与澄清补充。"""
        slots = dict(intent.slots or {})

        # 1. 从 account_context 补常见槽位
        for key in ["industry", "brand", "account_stage", "goal"]:
            if key not in slots and key in account_context:
                slots[key] = account_context[key]

        # 2. 检查必填槽位
        required = REQUIRED_SLOTS_BY_INTENT.get(intent.intent_type, [])
        missing: List[str] = [name for name in required if not slots.get(name)]

        needs_clarification = intent.needs_clarification or bool(missing)
        clarification_question = intent.clarification_question

        if missing and not clarification_question:
            clarification_question = self._build_clarification_question(intent.intent_type, missing)

        # 3. 返回新的 IntentOutput
        return intent.model_copy(
            update={
                "slots": slots,
                "needs_clarification": needs_clarification,
                "missing_slots": missing or intent.missing_slots,
                "clarification_question": clarification_question or intent.clarification_question,
            }
        )

    @staticmethod
    def _build_clarification_question(intent_type: str, missing: List[str]) -> str:
        """根据意图类型和缺失槽位生成通用澄清问句。"""
        if not missing:
            return ""
        slot_cn = {
            "industry": "行业（例如美妆、美食、装修）",
            "goal": "目标（例如涨粉、种草、转化）",
            "content_form": "内容形式（图文、视频等）",
            "account_stage": "账号阶段（起号、冷启动、放量、变现）",
            "reference": "参考内容（哪一篇笔记或素材）",
            "budget": "预算金额",
            "targeting": "投流定向人群",
        }
        readable = "、".join(slot_cn.get(s, s) for s in missing)
        prefix = "为了更好地帮您" + {
            IntentType.TOPIC_PLANNING.value: "做选题策划",
            IntentType.CONTENT_GENERATION.value: "生成内容",
            IntentType.ADS_PLANNING.value: "做投流规划",
            IntentType.ACCOUNT_STRATEGY.value: "制定账号战略",
        }.get(intent_type, "完成这次需求")
        return f"{prefix}，还需要补充一下这些信息：{readable}。请简单说明一下。"

    # -------- 规则占位实现（兜底）--------

    def _rule_based_intent(
        self, text: str, account_context: Dict[str, Any]
    ) -> IntentOutput:
        """在无 LLM 或 LLM 失败时使用的通用占位意图识别。

        不再依赖具体业务短语，而是提供一个安全的、结构化的默认输出：
        - 将原始输入写入 demand_summary 与 slots["raw_input"]；
        - 默认按「选题 + 内容生成」的链路处理，供下游 Planner 使用；
        - 所有更精细的分类与槽位补全交给 LLM 路径或后续迭代。
        """
        return IntentOutput(
            demand_summary=text or "用户提出了一条内容或账号相关的需求。",
            intent_type=IntentType.CHAINED.value,
            intent_breakdown=["topic_planning", "content_generation"],
            slots={"raw_input": text},
            needs_clarification=False,
            suggested_agents=["选题策划", "内容生成", "内容评估与检验"],
        )


def _format_advantages(advantages: list[Any]) -> str:
    """将优势列表格式化为可读文案。"""
    if not advantages:
        return ""
    if isinstance(advantages, list):
        if len(advantages) == 1:
            return str(advantages[0])
        return "、".join(str(a) for a in advantages)
    return str(advantages)
