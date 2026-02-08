"""FastAPI 入口：POST /intent、/fulfillability、/planner/run。"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from xhs_assistant.fulfillability.service import FulfillabilityService
from xhs_assistant.intent.service import IntentService
from xhs_assistant.planner.graph import build_workflow

app = FastAPI(title="小红书助手 API", version="0.1.0")

intent_service = IntentService()
fulfillability_service = FulfillabilityService()


class IntentRequest(BaseModel):
    """POST /intent 请求体。"""

    user_input: str = Field(description="用户自然语言输入")
    account_context: dict[str, Any] = Field(default_factory=dict, description="账号上下文")


@app.post("/intent")
def post_intent(req: IntentRequest) -> dict[str, Any]:
    """意图理解：返回 IntentOutput 结构化结果。"""
    out = intent_service.run(req.user_input, req.account_context)
    return out.model_dump()


class FulfillabilityRequest(BaseModel):
    """POST /fulfillability 请求体。"""

    intent_output: dict[str, Any] = Field(description="意图理解输出")
    account_context: dict[str, Any] = Field(default_factory=dict, description="账号上下文")


@app.post("/fulfillability")
def post_fulfillability(req: FulfillabilityRequest) -> dict[str, Any]:
    """可执行性检查：传入意图输出与账号上下文，返回 can_fulfill 等。"""
    from xhs_assistant.intent.schema import IntentOutput

    intent = IntentOutput.model_validate(req.intent_output)
    result = fulfillability_service.check(intent, req.account_context)
    return result.model_dump()


class PlannerRunRequest(BaseModel):
    """POST /planner/run 请求体。"""

    intent_output: dict[str, Any] = Field(description="意图理解输出（IntentOutput JSON）")
    account_context: dict[str, Any] = Field(default_factory=dict, description="账号上下文")
    past_steps: list[Any] | None = Field(default=None, description="可选：已有执行步骤，用于续跑")


@app.post("/planner/run")
def post_planner_run(req: PlannerRunRequest) -> dict[str, Any]:
    """Planner 服务：基于意图输出执行规划与占位执行。"""
    workflow = build_workflow()
    initial: dict[str, Any] = {
        # 可选：将 demand_summary 作为 user_input 供状态使用
        "user_input": req.intent_output.get("demand_summary", ""),
        "intent_output": req.intent_output,
        "account_context": req.account_context,
        "past_steps": req.past_steps or [],
    }
    result = workflow.invoke(initial)
    return result


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
