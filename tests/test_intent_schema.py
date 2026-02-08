"""意图 Schema 与 IntentService 占位测试。"""
from __future__ import annotations

import pytest

from xhs_assistant.intent.schema import IntentOutput, IntentType
from xhs_assistant.intent.service import IntentService


def test_intent_output_schema() -> None:
    """IntentOutput 可序列化且含 demand_summary、slots、needs_clarification。"""
    out = IntentOutput(
        demand_summary="测试摘要",
        intent_type=IntentType.CHAINED.value,
        slots={"industry": "美妆"},
        needs_clarification=False,
    )
    assert out.demand_summary == "测试摘要"
    assert out.slots["industry"] == "美妆"
    d = out.model_dump()
    assert "demand_summary" in d
    assert "slots" in d


def test_intent_service_run_returns_intent_output() -> None:
    """IntentService.run 返回 IntentOutput。"""
    svc = IntentService()
    out = svc.run("帮我起个美妆账号")
    assert isinstance(out, IntentOutput)
    assert out.demand_summary
    # 只要是合法 IntentType 即可（具体分类由实现决定）
    assert out.intent_type in {t.value for t in IntentType}


def test_intent_service_needs_clarification_when_slot_missing() -> None:
    """缺槽时 needs_clarification=True。"""
    svc = IntentService()
    out = svc.run("")
    assert out.needs_clarification is True
    assert out.clarification_question
