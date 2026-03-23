"""Nanobot Backend: 使用 LiteLLM 直接调用 LLM。

简化实现，避免 nanobot AgentLoop 的复杂性和事件循环问题。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from litellm import completion

from xhs_assistant.backends.base import (
    AgentBackend,
    ClarificationOutputData,
    ExecutionOutputData,
    IntentOutputData,
    PlanOutputData,
)
from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


# ============================================================================
# Prompt 模板
# ============================================================================

INTENT_SYSTEM_PROMPT = """你是一个专业的营销助手意图识别系统。

你的任务是分析用户输入，识别用户意图并提取关键信息。

## 输出格式
请严格按照以下 JSON 格式输出，不要添加任何额外文字：

```json
{
  "demand_summary": "用户需求的一句话摘要",
  "intent_type": "意图类型",
  "slots": {"platform": null, "industry": null, "goal": null, "topic": null, "account_stage": null, "account_persona": null, "content_form": "图文"},
  "needs_clarification": false,
  "clarification_question": null,
  "missing_slots": [],
  "suggested_agents": ["内容生成"]
}
```

## 意图类型
### 营销相关意图
- topic_planning: 选题策划
- content_generation: 内容生成
- ads_planning: 投流规划
- account_strategy: 账号战略
- chained: 链式意图（需要多个Agent协作）

### 非营销意图
- greeting: 问候（你好、在吗、您好）
- help: 求助/功能询问（你能做什么、怎么用、帮助）
- feedback: 反馈/投诉（不好用、有问题、建议）
- out_of_scope: 超出范围（天气、写代码、翻译、闲聊无关内容）

## ⚠️ 关键规则

### 第一步：判断是否为营销相关意图
如果用户输入**不属于**以上营销相关意图，设置：
- intent_type = 对应的非营销意图类型
- needs_clarification = false
- suggested_agents = []
- 直接返回，无需填充 slots

### 第二步（仅营销意图）：槽位有效性判断
- platform: 必须明确（小红书/抖音/微信等）
- industry: 行业领域（美妆/美食/穿搭/数码等），推断不出填 null
- goal: 营销目标（涨粉/种草/转化/品牌曝光等），推断不出填 null
- topic: 内容主题（咖啡/护肤/旅行等），推断不出填 null
- account_stage: 账号阶段（起号/冷启动/放量/变现），推断不出填 null
- account_persona: 账号人设（职场女性、学生党、宝妈等），推断不出填 null
- content_form: 内容形式，默认 "图文"

### 重要：避免重复澄清
如果账号上下文中的 slots 已有值，必须使用这些值，不要重复询问相同的问题！

### 澄清决策规则（仅营销意图）

**优先检查特殊需求：**
- 如果用户提到"账号人设"、"账号定位"但 account_persona 和 account_stage 都为 null → 需要澄清
- 如果用户提到"选题"但没有 topic → 需要澄清

**常规槽位检查：**
统计有效槽位数量（非 null 的槽位，不含 content_form）：
- **有效槽位 >= 2 且 platform 有值**：needs_clarification = false
- **有效槽位 < 2 或 platform 无值**：needs_clarification = true

选择缺失的重要槽位生成澄清问题，优先级：platform > account_persona > account_stage > industry > goal > topic

### 澄清问题模板
- platform 缺失："请问您希望在哪个平台发布？"
- account_persona 缺失："请问您的账号人设是什么？（如职场女性、学生党、宝妈等）"
- account_stage 缺失："请问您的账号处于什么阶段？（起号、冷启动、放量、变现）"
- industry 缺失："请问属于什么行业领域？"
- goal 缺失："请问您的营销目标是什么？"
- topic 缺失："请问您想做什么主题的内容？"

### 特殊情况
1. 如果用户输入非常模糊（如"帮我写一篇笔记"），只有 content_form 有值，则需要澄清多个槽位
2. 如果用户提到"账号人设"但缺少 account_persona 或 account_stage，必须澄清这两个槽位

## 示例

用户："你好"
输出：{"demand_summary": "用户问候", "intent_type": "greeting", "slots": {}, "needs_clarification": false, "suggested_agents": []}

用户："你能做什么？"
输出：{"demand_summary": "询问系统功能", "intent_type": "help", "slots": {}, "needs_clarification": false, "suggested_agents": []}

用户："今天北京天气怎么样？"
输出：{"demand_summary": "询问天气，超出服务范围", "intent_type": "out_of_scope", "slots": {}, "needs_clarification": false, "suggested_agents": []}

用户："帮我写一篇咖啡种草笔记"
输出：{"demand_summary": "生成咖啡种草笔记", "intent_type": "content_generation", "slots": {"platform": null, "industry": "美食", "goal": "种草", "topic": "咖啡", "content_form": "图文"}, "needs_clarification": true, "clarification_question": "请问您希望在哪个平台发布？", "missing_slots": ["platform"], "suggested_agents": ["内容生成"]}

用户："在小红书写一篇咖啡笔记"
输出：{"demand_summary": "在小红书生成咖啡笔记", "intent_type": "content_generation", "slots": {"platform": "小红书", "industry": "美食", "goal": null, "topic": "咖啡", "content_form": "图文"}, "needs_clarification": false, "missing_slots": [], "suggested_agents": ["内容生成"]}"""

PLAN_SYSTEM_PROMPT = """你是一个任务规划系统。根据意图生成执行计划。

输出 JSON 格式：
```json
{
  "steps": [{"step_id": "s1", "agent": "Agent名称", "input_summary": "描述"}],
  "reasoning": "规划理由"
}
```

可用 Agent：选题策划、内容生成、投流、账号战略、内容评估与检验"""

EXECUTE_SYSTEM_PROMPT = """你是一个专业的小红书内容创作者。根据任务要求生成高质量内容。

要求：
1. 内容符合小红书风格：emoji丰富、标题吸引人、正文有结构
2. 语言亲切自然，有真实感
3. 包含合适的标签

直接输出内容，不要使用任何工具。"""


class NanobotBackend(AgentBackend):
    """使用 LiteLLM 直接调用 LLM 的后端实现。

    特点：
    - 简单直接，避免 nanobot AgentLoop 的复杂性
    - 支持多种 LLM 提供商（通过 LiteLLM）
    - 快速响应，无额外开销
    """

    def __init__(self) -> None:
        """初始化 Backend。"""
        cfg = config.agent_backend

        self._model = cfg.nanobot_model
        self._api_key = cfg.nanobot_api_key
        self._api_base = cfg.nanobot_api_base

        logger.info(
            f"NanobotBackend initialized: model={self._model}, "
            f"api_base={self._api_base or 'default'}"
        )

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """调用 LLM。"""
        try:
            response = completion(
                model=self._model,
                api_key=self._api_key,
                api_base=self._api_base,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON。"""
        # 尝试匹配 ```json ... ``` 块
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            return json_match.group(1).strip()

        # 尝试匹配 { ... } 块
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            return brace_match.group(0)

        return text

    # ========================================================================
    # AgentBackend 接口实现
    # ========================================================================

    async def understand_intent(
        self,
        user_input: str,
        account_context: dict[str, Any],
    ) -> IntentOutputData:
        """理解用户意图。"""
        logger.debug(f"understand_intent: {user_input[:50]}...")

        # 检查是否已有足够槽位（避免重复澄清）
        existing_slots = account_context.get("slots", {})
        if isinstance(existing_slots, dict):
            # 过滤掉空值，统计有效槽位（不含 content_form）
            valid_slot_values = {k: v for k, v in existing_slots.items() if v and k != "content_form"}
            valid_slots_count = len(valid_slot_values)

            logger.info(f"已有槽位: {valid_slot_values}, 数量: {valid_slots_count}")

            # 检查是否有 platform
            has_platform = existing_slots.get("platform")

            # 检查是否提到账号人设但缺少相关信息
            user_input_lower = user_input.lower()
            mentions_persona = any(kw in user_input_lower for kw in ["人设", "定位", "账号战略"])
            needs_persona_info = mentions_persona and not (
                existing_slots.get("account_persona") or existing_slots.get("account_stage")
            )

            # 如果需要账号人设信息，不跳过澄清
            if needs_persona_info:
                logger.info("用户提到账号人设但缺少相关信息，需要澄清")
            # 如果 platform 有值且有1个以上其他槽位，跳过澄清
            elif has_platform and valid_slots_count >= 1:
                logger.info(f"已有足够槽位信息，跳过澄清: {valid_slot_values}")
                return IntentOutputData(
                    demand_summary=account_context.get("original_demand", user_input),
                    intent_type="content_generation",
                    slots=existing_slots,
                    needs_clarification=False,
                    suggested_agents=["内容生成"],
                )

        context_str = "\n".join(f"- {k}: {v}" for k, v in account_context.items() if v)
        user_message = f"用户输入：{user_input}\n\n账号上下文：{context_str or '无'}\n\n请输出 JSON。"

        try:
            response = self._call_llm(INTENT_SYSTEM_PROMPT, user_message)
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # 如果账号上下文中有槽位信息，合并到结果中（已有的值优先）
            slots = data.get("slots", {})
            if existing_slots:
                # 合并已有槽位，已有的值优先（用户已经回答过的）
                merged_slots = {**slots, **{k: v for k, v in existing_slots.items() if v}}
                slots = merged_slots

            return IntentOutputData(
                demand_summary=data.get("demand_summary", ""),
                intent_type=data.get("intent_type", "chained"),
                intent_breakdown=data.get("intent_breakdown"),
                slots=slots,
                needs_clarification=data.get("needs_clarification", False),
                clarification_question=data.get("clarification_question"),
                missing_slots=data.get("missing_slots"),
                suggested_agents=data.get("suggested_agents", ["内容生成"]),
            )

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Intent parsing failed: {e}")
            # 默认返回
            return IntentOutputData(
                demand_summary=user_input,
                intent_type="chained",
                slots={"raw_input": user_input},
                needs_clarification=False,
                suggested_agents=["选题策划", "内容生成", "内容评估与检验"],
            )

    async def plan_tasks(
        self,
        intent_output: dict[str, Any],
        account_context: dict[str, Any],
    ) -> PlanOutputData:
        """规划任务步骤。"""
        logger.debug(f"plan_tasks for intent: {intent_output.get('intent_type')}")

        user_message = f"意图识别结果：\n{json.dumps(intent_output, ensure_ascii=False, indent=2)}\n\n请生成执行计划。"

        try:
            response = self._call_llm(PLAN_SYSTEM_PROMPT, user_message)
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return PlanOutputData(
                steps=data.get("steps", []),
                reasoning=data.get("reasoning"),
            )

        except Exception as e:
            logger.warning(f"Plan parsing failed: {e}")
            # 默认计划
            suggested = intent_output.get("suggested_agents", ["内容生成"])
            steps = [
                {
                    "step_id": f"s{i+1}",
                    "agent": agent,
                    "input_summary": f"执行 {agent}",
                    "depends_on": [],
                    "acceptance_criteria": "完成",
                }
                for i, agent in enumerate(suggested)
            ]
            return PlanOutputData(steps=steps, reasoning="使用默认规划")

    async def execute_step(
        self,
        step: dict[str, Any],
        state: dict[str, Any],
    ) -> ExecutionOutputData:
        """执行单个步骤。"""
        step_id = step.get("step_id", "unknown")
        agent_name = step.get("agent", "")
        logger.debug(f"execute_step: {step_id} - {agent_name}")

        # 构建执行消息
        intent = state.get("intent_output", {})
        demand = intent.get("demand_summary", "")
        slots = intent.get("slots", {})

        user_message = f"""任务：{step.get('input_summary', '')}

需求：{demand}
平台：{slots.get('platform', '小红书')}
行业：{slots.get('industry', '')}
目标：{slots.get('goal', '')}

请生成符合要求的内容。"""

        try:
            response = self._call_llm(EXECUTE_SYSTEM_PROMPT, user_message)

            return ExecutionOutputData(
                success=True,
                output={"response": response, "agent": agent_name},
                error=None,
                step_id=step_id,
            )

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
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

        # 根据缺失槽位生成问句
        if "platform" in missing_slots:
            return ClarificationOutputData(
                question="请问您希望在哪个平台发布？如小红书、抖音、微信等",
                options=["小红书", "抖音", "微信", "朋友圈", "微博"],
                context_updated=None,
            )
        elif "industry" in missing_slots:
            return ClarificationOutputData(
                question="请问属于什么行业？如美妆、美食、穿搭等",
                options=["美妆", "美食", "穿搭", "数码", "家居", "健身"],
                context_updated=None,
            )
        elif "goal" in missing_slots:
            return ClarificationOutputData(
                question="请问您的主要目标是什么？",
                options=["涨粉", "种草", "转化", "品牌曝光"],
                context_updated=None,
            )
        elif "account_persona" in missing_slots:
            return ClarificationOutputData(
                question="请问您的账号人设是什么？（如职场女性、学生党、宝妈等）",
                options=["职场女性", "学生党", "宝妈", "健身达人", "美食博主", "旅行达人"],
                context_updated=None,
            )
        elif "account_stage" in missing_slots:
            return ClarificationOutputData(
                question="请问您的账号处于什么阶段？（起号、冷启动、放量、变现）",
                options=["起号", "冷启动", "放量", "变现"],
                context_updated=None,
            )

        return ClarificationOutputData(
            question="请补充更多信息。",
            options=None,
            context_updated=None,
        )

    @property
    def backend_name(self) -> str:
        """后端名称。"""
        return "nanobot"