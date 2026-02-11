"""FastAPI 入口：POST /intent、/fulfillability、/planner/run；认证 /auth/register、/auth/login。"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.auth_db import get_user_by_token, init_db, login as auth_login, logout as auth_logout, register as auth_register
from xhs_assistant.fulfillability.service import FulfillabilityService
from xhs_assistant.intent.service import IntentService
from xhs_assistant.planner.graph import build_workflow

init_db()

app = FastAPI(title="小红书助手 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
def root() -> dict[str, Any]:
    """根路径：说明为 API 服务，Web 界面请访问前端地址。"""
    return {
        "message": "小红书助手 API",
        "docs": "/docs",
        "health": "/health",
        "web_ui": "http://localhost:8000",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """避免浏览器请求 favicon 时返回 404。"""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok"}


# ---------- 认证 ----------

class RegisterRequest(BaseModel):
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class LoginRequest(BaseModel):
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


@app.post("/auth/register")
def post_register(req: RegisterRequest) -> dict[str, Any]:
    """注册。"""
    ok, msg = auth_register(req.username, req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": "注册成功"}


@app.post("/auth/login")
def post_login(req: LoginRequest) -> dict[str, Any]:
    """登录，返回 token 与用户名。"""
    ok, msg, token = auth_login(req.username, req.password)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    user = get_user_by_token(token)
    return {"ok": True, "token": token, "username": user["username"]}


class LogoutRequest(BaseModel):
    token: str = Field(description="登录时返回的 token")


@app.post("/auth/logout")
def post_logout(req: LogoutRequest) -> dict[str, Any]:
    """登出。"""
    auth_logout(req.token)
    return {"ok": True}


@app.get("/auth/me")
def get_me(authorization: str | None = None) -> dict[str, Any]:
    """根据 Authorization: Bearer <token> 返回当前用户，无效返回 401。"""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="未提供 token")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5173)
