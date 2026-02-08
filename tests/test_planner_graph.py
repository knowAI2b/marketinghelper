"""Planner LangGraph 工作流编译与占位执行测试。"""
from __future__ import annotations

import pytest

from xhs_assistant.planner.graph import build_workflow, execute_node, plan_node, replan_node, should_end


def test_build_workflow_compiles() -> None:
    """build_workflow() 返回可调用的编译图。"""
    workflow = build_workflow()
    assert workflow is not None
    assert callable(workflow.invoke)


def test_plan_node_produces_plan() -> None:
    """plan_node 根据 intent_output 产出 plan。"""
    state = {
        "intent_output": {"suggested_agents": ["选题策划", "内容评估与检验"]},
    }
    out = plan_node(state)
    assert "plan" in out
    steps = out["plan"].get("steps") or []
    assert len(steps) == 2
    assert steps[0].get("agent") == "选题策划"


def test_execute_node_appends_past_steps() -> None:
    """execute_node 执行当前 step 并追加 past_steps。"""
    state = {
        "plan": {
            "steps": [
                {"step_id": "s1", "agent": "选题策划", "input_summary": "执行选题策划", "depends_on": [], "acceptance_criteria": "通过"},
            ],
        },
        "past_steps": [],
    }
    out = execute_node(state)
    assert "past_steps" in out
    assert len(out["past_steps"]) == 1
    step, result = out["past_steps"][0]
    assert step["agent"] == "选题策划"
    assert "output" in result or "agent" in result


def test_replan_node_sets_response_when_done() -> None:
    """replan_node 在步骤全部完成时写入 response。"""
    state = {
        "plan": {"steps": [{"step_id": "s1", "agent": "选题策划"}]},
        "past_steps": [({"step_id": "s1", "agent": "选题策划"}, {"output": "ok"})],
    }
    out = replan_node(state)
    assert "response" in out


def test_workflow_invoke_end_to_end() -> None:
    """工作流 invoke 一轮：意图 → plan → execute → replan → 结束。"""
    workflow = build_workflow()
    initial = {
        "user_input": "生成选题",
        "intent_output": {"suggested_agents": ["选题策划"]},
        "past_steps": [],
    }
    result = workflow.invoke(initial)
    assert "response" in result
    assert result.get("past_steps")
    assert len(result["past_steps"]) == 1
