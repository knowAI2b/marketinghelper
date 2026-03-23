"""Agent 后端抽象层：定义统一的 Agent 能力接口。

支持多种 Agent 框架实现（native/nanobot/nanoclaw），
通过 BackendManager 根据配置选择具体实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol


# ============================================================================
# 结果协议（Protocol）
# ============================================================================

class IntentResult(Protocol):
    """意图识别结果协议。

    与 IntentOutput 结构对齐，确保不同后端返回统一格式。
    """

    demand_summary: str
    """需求摘要"""

    intent_type: str
    """意图类型：mixed/chained/topic_planning/ads_planning 等"""

    intent_breakdown: list[str] | None
    """意图拆解列表（已确定的子意图）"""

    slots: dict[str, Any]
    """槽位键值对"""

    needs_clarification: bool
    """是否需要澄清"""

    clarification_question: str | None
    """澄清问句"""

    missing_slots: list[str] | None
    """缺失槽位"""

    suggested_agents: list[str]
    """建议调用的 Agent"""

    ambiguous_intent: str | None
    """歧义说明（歧义时）"""


class PlanResult(Protocol):
    """任务规划结果协议。"""

    steps: list[dict[str, Any]]
    """执行步骤列表，每个步骤包含 step_id, agent, input_summary, depends_on, acceptance_criteria"""

    reasoning: str | None
    """规划推理过程（可选）"""


class ExecutionResult(Protocol):
    """执行结果协议。"""

    success: bool
    """是否成功"""

    output: Any
    """执行输出"""

    error: str | None
    """错误信息（失败时）"""

    step_id: str | None
    """步骤 ID"""


class ClarificationResult(Protocol):
    """澄清对话结果协议。"""

    question: str
    """澄清问句"""

    options: list[str] | None
    """可选的回复选项"""

    context_updated: dict[str, Any] | None
    """更新后的上下文"""


# ============================================================================
# 具体结果类（用于后端实现返回）
# ============================================================================

@dataclass
class IntentOutputData:
    """意图识别输出数据类，实现 IntentResult 协议。"""

    demand_summary: str = ""
    intent_type: str = "ambiguous"
    intent_breakdown: list[str] | None = None
    slots: dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    clarification_question: str | None = None
    missing_slots: list[str] | None = None
    suggested_agents: list[str] = field(default_factory=list)
    ambiguous_intent: str | None = None
    user_can_edit_task_breakdown: bool = False
    intent_breakdown_candidates: list[str] | None = None


@dataclass
class PlanOutputData:
    """任务规划输出数据类，实现 PlanResult 协议。"""

    steps: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str | None = None


@dataclass
class ExecutionOutputData:
    """执行输出数据类，实现 ExecutionResult 协议。"""

    success: bool = True
    output: Any = None
    error: str | None = None
    step_id: str | None = None


@dataclass
class ClarificationOutputData:
    """澄清对话输出数据类，实现 ClarificationResult 协议。"""

    question: str = ""
    options: list[str] | None = None
    context_updated: dict[str, Any] | None = None


# ============================================================================
# AgentBackend 抽象基类
# ============================================================================

class AgentBackend(ABC):
    """Agent 后端抽象基类。

    定义统一的 Agent 能力接口，支持：
    - 意图理解 (understand_intent)
    - 任务规划 (plan_tasks)
    - 步骤执行 (execute_step)
    - 需求澄清 (clarify)

    具体实现：
    - NativeBackend: 基于 LangGraph 的现有实现
    - NanobotBackend: 基于 nanobot 框架的实现
    - NanoclawBackend: 基于 nanoclaw 的实现（后续扩展）
    """

    @abstractmethod
    async def understand_intent(
        self,
        user_input: str,
        account_context: dict[str, Any],
    ) -> IntentOutputData:
        """理解用户意图。

        Args:
            user_input: 用户自然语言输入
            account_context: 账号上下文（行业、品牌、目标等）

        Returns:
            IntentOutputData: 结构化意图识别结果
        """
        ...

    @abstractmethod
    async def plan_tasks(
        self,
        intent_output: dict[str, Any],
        account_context: dict[str, Any],
    ) -> PlanOutputData:
        """规划任务步骤。

        根据意图输出生成可执行的计划，包含多个步骤。

        Args:
            intent_output: 意图理解输出
            account_context: 账号上下文

        Returns:
            PlanOutputData: 包含步骤列表的规划结果
        """
        ...

    @abstractmethod
    async def execute_step(
        self,
        step: dict[str, Any],
        state: dict[str, Any],
    ) -> ExecutionOutputData:
        """执行单个步骤。

        Args:
            step: 步骤信息（step_id, agent, input_summary 等）
            state: 工作流状态（intent_output, past_steps 等）

        Returns:
            ExecutionOutputData: 执行结果
        """
        ...

    @abstractmethod
    async def clarify(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> ClarificationOutputData:
        """需求澄清对话。

        当意图不明确或缺少必要槽位时，生成澄清问句。

        Args:
            user_input: 用户输入
            context: 当前上下文（missing_slots, slots 等）

        Returns:
            ClarificationOutputData: 澄清问句和选项
        """
        ...

    # ========================================================================
    # 可选方法（有默认实现）
    # ========================================================================

    async def health_check(self) -> bool:
        """检查后端是否健康可用。

        Returns:
            bool: 后端是否正常
        """
        return True

    async def close(self) -> None:
        """关闭后端，释放资源。"""
        pass

    @property
    def backend_name(self) -> str:
        """后端名称。"""
        return self.__class__.__name__.replace("Backend", "").lower()


# ============================================================================
# 后端类型枚举
# ============================================================================

class BackendType:
    """后端类型常量。"""

    NATIVE = "native"
    NANOBOT = "nanobot"
    NANOCLAW = "nanoclaw"

    @classmethod
    def all(cls) -> list[str]:
        """返回所有支持的后端类型。"""
        return [cls.NATIVE, cls.NANOBOT, cls.NANOCLAW]

    @classmethod
    def is_valid(cls, backend_type: str) -> bool:
        """检查后端类型是否有效。"""
        return backend_type in cls.all()