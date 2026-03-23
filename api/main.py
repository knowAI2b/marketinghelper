"""FastAPI 入口：POST /intent、/fulfillability、/planner/run；认证 /auth/register、/auth/login。

支持多种 Agent 后端（native/nanobot/nanoclaw）。
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, Header, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# 加载 .env 文件
load_dotenv()

# 初始化日志（必须在其他模块导入前）
from xhs_assistant.shared.logging_config import setup_logging, log_api_request, log_user_action
setup_logging(app_level="INFO", console_level="INFO")

import logging
logger = logging.getLogger(__name__)

from api.auth_db import (
    get_user_by_token,
    init_db,
    login as auth_login,
    logout as auth_logout,
    register as auth_register,
    save_uploaded_image_bytes,
)
from xhs_assistant.backends import BackendManager
from xhs_assistant.fulfillability.service import FulfillabilityService
from xhs_assistant.intent.service import IntentService
from xhs_assistant.planner.graph import build_workflow, run_workflow_with_progress
from xhs_assistant.shared.config import config
from xhs_assistant.agents.registry import get_registry_info

init_db()

app = FastAPI(title="小红书助手 API", version="0.1.0")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件。"""

    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()

        # 获取用户信息（如果有 token）
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = get_user_by_token(token)
            if user:
                user_id = user.username

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        # 记录 API 请求（排除健康检查等）
        if not request.url.path.startswith("/api/health"):
            log_api_request(
                endpoint=request.url.path,
                method=request.method,
                user_id=user_id,
                response_status=response.status_code,
                duration_ms=duration_ms,
            )

        return response


app.add_middleware(RequestLoggingMiddleware)

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
    # 记录用户行为
    session_id = req.account_context.get("session_id")
    log_user_action(
        action="intent_request",
        user_id=req.account_context.get("user_id"),
        session_id=session_id,
        details={"input": req.user_input[:100]},  # 只记录前100字符
    )

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
    # 记录用户行为
    session_id = req.account_context.get("session_id")
    intent_type = req.intent_output.get("intent_type", "unknown")
    log_user_action(
        action="planner_run",
        user_id=req.account_context.get("user_id"),
        session_id=session_id,
        details={"intent_type": intent_type},
    )

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


@app.post("/planner/stream")
async def post_planner_stream(req: PlannerRunRequest):
    """Planner 流式服务：SSE 实时推送执行进度。

    返回 Server-Sent Events 流：
    - event: stage - 执行阶段变更
    - event: result - 最终结果
    - event: error - 错误
    """
    session_id = req.account_context.get("session_id")
    intent_type = req.intent_output.get("intent_type", "unknown")
    log_user_action(
        action="planner_stream",
        user_id=req.account_context.get("user_id"),
        session_id=session_id,
        details={"intent_type": intent_type},
    )

    # 使用队列实现实时推送
    event_queue: asyncio.Queue = asyncio.Queue()

    async def event_generator():
        try:
            while True:
                event = await event_queue.get()
                if event is None:  # 结束信号
                    break
                yield event
        except asyncio.CancelledError:
            pass

    async def run_workflow():
        try:
            def on_progress(step: str, message: str, agent: str | None = None):
                """进度回调：将事件放入队列。"""
                event_data = json.dumps({
                    "step": step,
                    "message": message,
                    "agent": agent,
                }, ensure_ascii=False)
                # 在异步上下文中安全地放入队列
                try:
                    loop = asyncio.get_running_loop()
                    loop.call_soon_threadsafe(
                        lambda: event_queue.put_nowait(f"event: stage\ndata: {event_data}\n\n")
                    )
                except Exception as e:
                    logger.warning(f"Failed to queue progress event: {e}")

            # 执行工作流
            result = await run_workflow_with_progress(
                intent_output=req.intent_output,
                account_context=req.account_context,
                on_progress=on_progress,
                past_steps=req.past_steps,
            )

            # 发送最终结果
            result_data = json.dumps(result, ensure_ascii=False, default=str)
            await event_queue.put(f"event: result\ndata: {result_data}\n\n")

        except Exception as e:
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            await event_queue.put(f"event: error\ndata: {error_data}\n\n")

        finally:
            # 发送结束信号
            await event_queue.put(None)

    # 启动工作流任务
    workflow_task = asyncio.create_task(run_workflow())

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
def root() -> dict[str, Any]:
    """根路径：说明为 API 服务，Web 界面请访问前端地址。"""
    return {
        "message": "小红书助手 API",
        "docs": "/docs",
        "health": "/health",
        "web_ui": "http://localhost:8000",
        "backend": {
            "info": "/backend/info",
            "status": "/backend/status",
            "agents": "/backend/agents",
        },
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


@app.get("/api/logs/stats")
def get_log_stats() -> dict[str, Any]:
    """获取日志文件统计信息（仅用于调试）。"""
    from xhs_assistant.shared.logging_config import get_log_stats as _get_log_stats
    return _get_log_stats()


# ---------- 后端管理 ----------

@app.get("/backend/info")
def get_backend_info() -> dict[str, Any]:
    """获取 Agent 后端配置信息。"""
    cfg = config.agent_backend
    return {
        "backend_type": cfg.backend_type,
        "intent_backend": cfg.get_effective_backend("intent"),
        "planner_backend": cfg.get_effective_backend("planner"),
        "executor_backend": cfg.get_effective_backend("executor"),
        "nanobot": {
            "model": cfg.nanobot_model,
            "max_iterations": cfg.nanobot_max_iterations,
            "workspace": cfg.nanobot_workspace,
            "web_search_enabled": cfg.nanobot_web_search_enabled,
        },
        "active_backends": BackendManager.get_active_backends(),
    }


@app.get("/backend/status")
async def get_backend_status() -> dict[str, Any]:
    """获取所有已初始化后端的健康状态。"""
    health_status = BackendManager.health_check()
    return {
        "status": health_status,
        "all_healthy": all(health_status.values()) if health_status else True,
    }


@app.get("/backend/agents")
def get_agents() -> dict[str, Any]:
    """获取 Agent 注册表信息。"""
    return get_registry_info()


@app.post("/backend/clear-cache")
def clear_backend_cache() -> dict[str, Any]:
    """清空后端实例缓存（用于重新初始化）。"""
    BackendManager.clear_cache()
    return {"ok": True, "message": "Backend cache cleared"}


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
        log_user_action(action="register_failed", details={"username": req.username, "reason": msg})
        raise HTTPException(status_code=400, detail=msg)
    log_user_action(action="register", user_id=req.username, details={"username": req.username})
    return {"ok": True, "message": "注册成功"}


@app.post("/auth/login")
def post_login(req: LoginRequest) -> dict[str, Any]:
    """登录，返回 token 与用户名。"""
    ok, msg, token = auth_login(req.username, req.password)
    if not ok:
        log_user_action(action="login_failed", details={"username": req.username, "reason": msg})
        raise HTTPException(status_code=401, detail=msg)
    user = get_user_by_token(token)
    log_user_action(action="login", user_id=req.username)
    return {"ok": True, "token": token, "username": user["username"]}


class LogoutRequest(BaseModel):
    token: str = Field(description="登录时返回的 token")


@app.post("/auth/logout")
def post_logout(req: LogoutRequest) -> dict[str, Any]:
    """登出。"""
    user = get_user_by_token(req.token)
    user_id = user["username"] if user else None
    auth_logout(req.token)
    if user_id:
        log_user_action(action="logout", user_id=user_id)
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


@app.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """上传单张图片，落盘到 data/uploads/yyyy/mm/dd 并写入 uploaded_images 表。"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持上传图片")

    user_id: int | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        user = get_user_by_token(token)
        if user:
            user_id = int(user["id"])

    data = await file.read()
    info = save_uploaded_image_bytes(
        data=data,
        original_name=file.filename or "",
        content_type=file.content_type,
        user_id=user_id,
    )
    return {"ok": True, "image": info}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5173)
