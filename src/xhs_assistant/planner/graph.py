"""LangGraph Plan-and-Execute 工作流：支持多种 Agent 后端。

工作流程：
plan_node → execute_node → replan_node → 条件边

支持后端：
- native: 使用 LangGraph 原有实现
- nanobot: 使用 nanobot 框架进行规划
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from xhs_assistant.agents.rag_retrieval import AGENT_RAG_RETRIEVAL
from xhs_assistant.backends import BackendManager, PlanOutputData
from xhs_assistant.planner.schema import Plan, Step
from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


# 进度回调类型
ProgressCallback = Callable[[str, str, str | None], None]  # step, message, agent


class GraphState(TypedDict, total=False):
    """LangGraph 状态：与 WorkspaceState 字段一致。"""

    user_input: str
    intent_output: dict[str, Any]
    plan: dict[str, Any]
    past_steps: list[Any]
    response: str
    account_context: dict[str, Any]
    backend_type: str  # 新增：记录使用的后端类型
    rag_data: dict[str, Any]  # 新增：RAG 检索结果


State = dict[str, Any]


def _should_add_rag_step(intent_output: dict[str, Any]) -> bool:
    """判断是否需要添加 RAG 检索步骤。

    触发条件：
    1. suggested_agents 包含"选题策划"或"内容生成"
    2. slots 中有产品信息（product/category/topic）

    Args:
        intent_output: 意图识别输出

    Returns:
        bool: 是否需要添加 RAG 步骤
    """
    # RAG 服务未启用时不添加
    if not config.rag.enabled:
        return False

    suggested_agents = intent_output.get("suggested_agents", [])
    slots = intent_output.get("slots", {})

    # 检查是否有需要 RAG 的 Agent
    needs_rag_agents = "选题策划" in suggested_agents or "内容生成" in suggested_agents
    if not needs_rag_agents:
        return False

    # 检查是否有产品信息
    has_product_info = bool(
        slots.get("product") or slots.get("category") or slots.get("topic")
    )

    return has_product_info


def _make_plan_from_intent(intent_output: dict[str, Any]) -> dict[str, Any]:
    """根据意图输出生成占位 Plan（Native 后端）。

    Args:
        intent_output: 意图识别输出

    Returns:
        dict: Plan 结构
    """
    suggested = intent_output.get("suggested_agents") or ["选题策划", "内容生成", "内容评估与检验"]

    # 判断是否需要添加 RAG 检索步骤
    add_rag = _should_add_rag_step(intent_output)

    # 构建步骤列表
    steps = []
    step_idx = 0

    # 如果需要 RAG，在最前面添加 RAG 检索步骤
    if add_rag:
        steps.append(
            Step(
                step_id=f"s{step_idx}",
                agent=AGENT_RAG_RETRIEVAL,
                input_summary="获取选题卡数据（趋势、热门话题等）",
                depends_on=[],
                acceptance_criteria="成功获取选题卡数据或降级跳过",
            )
        )
        step_idx += 1

    # 添加原有的 Agent 步骤
    for i, a in enumerate(suggested):
        steps.append(
            Step(
                step_id=f"s{step_idx + i}",
                agent=a,
                input_summary=f"执行 {a}",
                depends_on=[f"s{step_idx + i - 1}"] if i > 0 else ([f"s{step_idx - 1}"] if add_rag else []),
                acceptance_criteria="通过",
            )
        )

    return Plan(steps=steps).model_dump()


async def _make_plan_with_backend(
    intent_output: dict[str, Any],
    account_context: dict[str, Any],
) -> dict[str, Any]:
    """使用外部后端生成计划。

    Args:
        intent_output: 意图识别输出
        account_context: 账号上下文

    Returns:
        dict: Plan 结构
    """
    backend_type = config.agent_backend.get_effective_backend("planner")
    logger.debug(f"Making plan with backend: {backend_type}")

    if backend_type == "native":
        # Native 后端：使用原有逻辑
        return _make_plan_from_intent(intent_output)

    # 外部后端
    try:
        backend = BackendManager.get_planner_backend()
        result: PlanOutputData = await backend.plan_tasks(intent_output, account_context)

        if result.steps:
            return {"steps": result.steps}

        # 如果返回空，降级到 native
        logger.warning("External backend returned empty plan, falling back to native")
        return _make_plan_from_intent(intent_output)

    except Exception as e:
        logger.error(f"External backend failed: {e}, falling back to native")
        return _make_plan_from_intent(intent_output)


def plan_node(state: State) -> State:
    """生成多步计划并写入 state。"""
    intent_output = state.get("intent_output") or {}
    account_context = state.get("account_context") or {}
    backend_type = config.agent_backend.get_effective_backend("planner")

    logger.debug(f"plan_node using backend: {backend_type}")

    # 根据后端类型选择规划方式
    if backend_type == "native":
        plan = _make_plan_from_intent(intent_output)
    else:
        # 外部后端需要异步调用
        try:
            loop = asyncio.get_running_loop()
            # 在异步上下文中，直接等待
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _make_plan_with_backend(intent_output, account_context)
                )
                plan = future.result()
        except RuntimeError:
            plan = asyncio.run(_make_plan_with_backend(intent_output, account_context))

    return {"plan": plan, "backend_type": backend_type}


async def execute_step_with_backend(
    step: dict[str, Any],
    state: State,
) -> Any:
    """使用后端执行单个步骤。

    Args:
        step: 步骤信息
        state: 工作流状态

    Returns:
        执行结果
    """
    backend_type = config.agent_backend.get_effective_backend("executor")
    logger.debug(f"execute_step with backend: {backend_type}")

    if backend_type == "native":
        # Native 后端：使用 registry
        from xhs_assistant.agents.registry import run_agent
        agent_name = step.get("agent", "")
        return run_agent(agent_name, step, state)

    # 外部后端
    try:
        backend = BackendManager.get_executor_backend()
        result = await backend.execute_step(step, state)

        if result.success:
            return result.output
        else:
            return {"error": result.error, "step_id": result.step_id}

    except Exception as e:
        logger.error(f"External backend execute failed: {e}")
        return {"error": str(e), "step_id": step.get("step_id")}


def execute_node(state: State) -> State:
    """执行当前一步：从 plan 取当前 step，调用对应后端执行。"""
    plan = state.get("plan") or {}
    steps_list = plan.get("steps") or []
    past_steps = list(state.get("past_steps") or [])
    current_index = len(past_steps)

    if current_index >= len(steps_list):
        return {}

    step_dict = steps_list[current_index]
    if isinstance(step_dict, dict):
        step = step_dict
    else:
        step = step_dict.model_dump() if hasattr(step_dict, "model_dump") else step_dict

    # 根据后端类型执行
    backend_type = state.get("backend_type") or config.agent_backend.get_effective_backend("executor")

    if backend_type == "native":
        # Native 后端：同步执行
        from xhs_assistant.agents.registry import run_agent
        agent_name = step.get("agent", "")
        result = run_agent(agent_name, step, state)
    else:
        # 外部后端：需要异步
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    execute_step_with_backend(step, state)
                )
                result = future.result()
        except RuntimeError:
            result = asyncio.run(execute_step_with_backend(step, state))

    past_steps.append((step, result))
    return {"past_steps": past_steps}


def replan_node(state: State) -> State:
    """判断是否还有未执行步骤；若全部完成则写入 response 并结束。"""
    plan = state.get("plan") or {}
    steps_list = plan.get("steps") or []
    past_steps = state.get("past_steps") or []

    if len(past_steps) >= len(steps_list):
        return {"response": "执行完成。"}
    return {}


def should_end(state: State) -> Literal["__end__", "execute"]:
    """条件边：若已有 response 则结束，否则回到 execute。"""
    if state.get("response"):
        return "__end__"
    return "execute"


def build_workflow():
    """构建 LangGraph 工作流并返回编译后的图。"""
    workflow = StateGraph(GraphState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("replan", replan_node)

    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "replan")
    workflow.add_conditional_edges("replan", should_end, ["execute", END])

    return workflow.compile()


# ============================================================================
# 异步版本的工作流（可选使用）
# ============================================================================

async def run_workflow_async(
    intent_output: dict[str, Any],
    account_context: dict[str, Any],
    past_steps: list[Any] | None = None,
) -> dict[str, Any]:
    """异步执行完整工作流。

    Args:
        intent_output: 意图识别输出
        account_context: 账号上下文
        past_steps: 已完成的步骤（用于续跑）

    Returns:
        dict: 工作流最终状态
    """
    workflow = build_workflow()
    initial: dict[str, Any] = {
        "user_input": intent_output.get("demand_summary", ""),
        "intent_output": intent_output,
        "account_context": account_context,
        "past_steps": past_steps or [],
    }
    result = workflow.invoke(initial)
    return result


# ============================================================================
# 支持进度回调的流式执行
# ============================================================================

async def run_workflow_with_progress(
    intent_output: dict[str, Any],
    account_context: dict[str, Any],
    on_progress: ProgressCallback | None = None,
    past_steps: list[Any] | None = None,
) -> dict[str, Any]:
    """带进度回调的工作流执行。

    手动分步执行，在每个阶段调用回调通知进度。

    Args:
        intent_output: 意图识别输出
        account_context: 账号上下文
        on_progress: 进度回调函数 (step, message, agent)
        past_steps: 已完成的步骤（用于续跑）

    Returns:
        dict: 工作流最终状态
    """
    state: dict[str, Any] = {
        "user_input": intent_output.get("demand_summary", ""),
        "intent_output": intent_output,
        "account_context": account_context,
        "past_steps": past_steps or [],
    }

    def notify(step: str, message: str, agent: str | None = None):
        if on_progress:
            try:
                on_progress(step, message, agent)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    try:
        # 1. 规划阶段
        notify("planning", "正在规划任务...")
        plan_result = await _make_plan_with_backend(intent_output, account_context)
        state["plan"] = plan_result
        state["backend_type"] = config.agent_backend.get_effective_backend("planner")

        steps_list = plan_result.get("steps", [])
        current_past_steps = list(state.get("past_steps", []))

        if not steps_list:
            notify("complete", "任务规划为空，无需执行")
            state["response"] = "任务规划为空。"
            return state

        # 2. 执行阶段 - 逐步执行
        for i, step_dict in enumerate(steps_list):
            if isinstance(step_dict, dict):
                step = step_dict
            else:
                step = step_dict.model_dump() if hasattr(step_dict, "model_dump") else step_dict

            agent_name = step.get("agent", "未知服务")
            notify("agent", f"正在调用 {agent_name} 服务...", agent_name)

            # 执行单个步骤
            backend_type = state.get("backend_type") or config.agent_backend.get_effective_backend("executor")

            if backend_type == "native":
                from xhs_assistant.agents.registry import run_agent
                result = run_agent(agent_name, step, state)
            else:
                result = await execute_step_with_backend(step, state)

            current_past_steps.append((step, result))
            state["past_steps"] = current_past_steps

            # 通知步骤完成
            notify("step_done", f"{agent_name} 执行完成", agent_name)

        # 3. 完成
        notify("complete", "任务执行完成")
        state["response"] = "执行完成。"
        return state

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        notify("error", f"执行失败: {str(e)}")
        state["response"] = f"执行失败: {str(e)}"
        return state