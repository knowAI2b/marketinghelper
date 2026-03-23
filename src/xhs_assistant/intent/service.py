"""意图识别服务：支持多种 Agent 后端。

设计目标：
- 支持多种后端：native（LangChain）或 nanobot
- 支持「槽位补全」：结合用户输入 + 账号上下文 + 必填槽配置
- 高鲁棒性：任何失败时回退到规则占位实现

后端选择：
- 通过 XHS_AGENT_BACKEND_TYPE 环境变量选择
- 可通过 XHS_INTENT_BACKEND 单独覆盖意图识别后端
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from xhs_assistant.backends import BackendManager, IntentOutputData
from xhs_assistant.intent.schema import IntentOutput, IntentType
from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


# 每种意图的「推荐必填槽位」，用于缺槽检测与澄清。
REQUIRED_SLOTS_BY_INTENT: Dict[str, List[str]] = {
    IntentType.TOPIC_PLANNING.value: ["platform", "industry", "goal"],
    IntentType.CONTENT_GENERATION.value: ["platform", "industry", "content_form"],
    IntentType.ADS_PLANNING.value: ["platform", "reference", "budget", "targeting"],
    IntentType.ACCOUNT_STRATEGY.value: ["platform", "industry", "goal", "account_stage"],
}


class IntentService:
    """意图理解服务。

    支持多种 Agent 后端：
    - native: 使用 LangChain + OpenAI（原有实现）
    - nanobot: 使用 nanobot 框架

    工作流程：
    1. 检查配置的后端类型
    2. 如果是 nanobot，调用 BackendManager
    3. 如果是 native，使用原有 LangChain 逻辑
    4. 任何失败时回退到规则占位
    """

    def __init__(self, use_llm: bool | None = None) -> None:
        """初始化意图识别服务。

        Args:
            use_llm: 是否使用 LLM（仅 native 后端），None 时从环境变量读取
        """
        # 检查是否使用外部 Agent 后端
        self._backend_type = config.agent_backend.get_effective_backend("intent")
        self._use_external_backend = self._backend_type != "native"

        if self._use_external_backend:
            logger.info(f"IntentService using external backend: {self._backend_type}")
            self._backend = BackendManager.get_intent_backend()
            self.use_llm = False  # 外部后端自己管理 LLM
            self._llm = None
            self._prompt = None
        else:
            # Native 后端：使用原有 LangChain 实现
            self._backend = None
            if use_llm is None:
                env_flag = os.getenv("XHS_ASSISTANT_USE_LLM_INTENT", "").lower()
                use_llm = env_flag in {"1", "true", "yes"}
            self.use_llm = use_llm
            self._init_native_llm()

        self._parser = PydanticOutputParser(pydantic_object=IntentOutput)

    def _init_native_llm(self) -> None:
        """初始化 Native 后端的 LLM。"""
        self._llm = None
        self._prompt = None

        if self.use_llm:
            try:
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
                logger.info(f"Native LLM initialized with model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize native LLM: {e}")

    def run(self, user_input: str, account_context: Dict[str, Any] | None = None) -> IntentOutput:
        """解析用户输入，返回结构化意图（同步接口）。

        Args:
            user_input: 用户自然语言输入
            account_context: 账号上下文

        Returns:
            IntentOutput: 结构化意图结果
        """
        # 尝试异步调用
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在异步上下文中，创建任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.run_async(user_input, account_context)
                )
                return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self.run_async(user_input, account_context))

    async def run_async(
        self,
        user_input: str,
        account_context: Dict[str, Any] | None = None,
    ) -> IntentOutput:
        """解析用户输入，返回结构化意图（异步接口）。

        Args:
            user_input: 用户自然语言输入
            account_context: 账号上下文

        Returns:
            IntentOutput: 结构化意图结果
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

        # 使用外部后端
        if self._use_external_backend and self._backend:
            try:
                result: IntentOutputData = await self._backend.understand_intent(
                    text, account_context
                )
                return self._convert_to_intent_output(result, account_context)
            except Exception as e:
                logger.error(f"External backend failed: {e}")
                # 降级到规则占位

        # Native 后端：LLM 路径
        if self.use_llm and self._llm and self._prompt:
            try:
                chain = self._prompt | self._llm | self._parser
                intent: IntentOutput = chain.invoke(
                    {"user_input": text, "account_context": account_context}
                )
                return self._fill_slots(intent, account_context)
            except Exception as e:
                logger.warning(f"Native LLM failed: {e}")
                # 降级到规则占位

        # 规则占位实现（兜底）
        intent = self._rule_based_intent(text, account_context)
        return self._fill_slots(intent, account_context)

    def _convert_to_intent_output(
        self,
        data: IntentOutputData,
        account_context: Dict[str, Any],
    ) -> IntentOutput:
        """将 IntentOutputData 转换为 IntentOutput。"""
        intent = IntentOutput(
            demand_summary=data.demand_summary,
            intent_type=data.intent_type,
            intent_breakdown=data.intent_breakdown,
            slots=data.slots,
            needs_clarification=data.needs_clarification,
            clarification_question=data.clarification_question,
            suggested_agents=data.suggested_agents,
            user_can_edit_task_breakdown=data.user_can_edit_task_breakdown,
            missing_slots=data.missing_slots,
            ambiguous_intent=data.ambiguous_intent,
            intent_breakdown_candidates=data.intent_breakdown_candidates,
        )
        return self._fill_slots(intent, account_context)

    # -------- 槽位补全与缺槽检测 --------

    def _fill_slots(self, intent: IntentOutput, account_context: Dict[str, Any]) -> IntentOutput:
        """合并 slots 与账号上下文，并根据意图类型做缺槽检测与澄清补充。"""
        slots = dict(intent.slots or {})

        # 1. 从 account_context 中的 slots 字段合并（前端传递的已收集槽位）
        context_slots = account_context.get("slots", {})
        if isinstance(context_slots, dict):
            for key, value in context_slots.items():
                if value and key not in slots:
                    slots[key] = value

        # 2. 从 account_context 顶层补常见槽位
        for key in ["platform", "industry", "brand", "account_stage", "goal", "topic", "content_form"]:
            if key not in slots and key in account_context:
                slots[key] = account_context[key]

        # 3. content_form 默认值
        if not slots.get("content_form"):
            slots["content_form"] = "图文"

        # 4. 检查必填槽位（排除 content_form，因为有默认值）
        required = REQUIRED_SLOTS_BY_INTENT.get(intent.intent_type, [])
        # content_form 有默认值，不需要检查
        required_to_check = [name for name in required if name != "content_form"]
        missing: List[str] = [name for name in required_to_check if not slots.get(name)]

        # 如果已有 platform，不再强制要求其他槽位
        if slots.get("platform"):
            needs_clarification = False
            missing = []
        else:
            needs_clarification = intent.needs_clarification or bool(missing)

        clarification_question = intent.clarification_question

        if missing and not clarification_question:
            clarification_question = self._build_clarification_question(intent.intent_type, missing)

        # 5. 返回新的 IntentOutput
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
            "platform": "投放平台（如小红书、微信、抖音、朋友圈）",
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

    # -------- 后端信息 --------

    @property
    def backend_type(self) -> str:
        """当前使用的后端类型。"""
        return self._backend_type

    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息。"""
        return {
            "backend_type": self._backend_type,
            "use_llm": self.use_llm,
            "external_backend": self._use_external_backend,
        }


def _format_advantages(advantages: list[Any]) -> str:
    """将优势列表格式化为可读文案。"""
    if not advantages:
        return ""
    if isinstance(advantages, list):
        if len(advantages) == 1:
            return str(advantages[0])
        return "、".join(str(a) for a in advantages)
    return str(advantages)