"""LangGraph Plan-and-Execute 工作流：plan_node → execute_node → replan_node → 条件边。"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from xhs_assistant.agents.registry import run_agent
from xhs_assistant.planner.schema import Plan, Step


class GraphState(TypedDict, total=False):
    """LangGraph 状态：与 WorkspaceState 字段一致。"""

    user_input: str
    intent_output: dict[str, Any]
    plan: dict[str, Any]
    past_steps: list[Any]
    response: str
    account_context: dict[str, Any]


State = dict[str, Any]


def _make_plan_from_intent(intent_output: dict[str, Any]) -> dict[str, Any]:
    """根据意图输出生成占位 Plan；后续接 LLM。"""
    suggested = intent_output.get("suggested_agents") or ["选题策划", "内容生成", "内容评估与检验"]
    steps = [
        Step(step_id=f"s{i+1}", agent=a, input_summary=f"执行 {a}", depends_on=[f"s{i}"] if i > 0 else [], acceptance_criteria="通过")
        for i, a in enumerate(suggested)
    ]
    return Plan(steps=steps).model_dump()


def plan_node(state: State) -> State:
    """生成多步计划并写入 state。"""
    intent_output = state.get("intent_output") or {}
    plan = _make_plan_from_intent(intent_output)
    return {"plan": plan}


def execute_node(state: State) -> State:
    """执行当前一步：从 plan 取当前 step，调用 registry 中对应 agent，结果追加到 past_steps。"""
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
    agent_name = step.get("agent", "")
    result = run_agent(agent_name, step, state)
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