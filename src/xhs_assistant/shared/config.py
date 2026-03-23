"""运行时配置：平台开关、外部服务配置、Agent 后端配置。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _get_bool(key: str, default: bool = False) -> bool:
    """从环境变量读取布尔值。"""
    val = os.environ.get(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


def _get_int(key: str, default: int) -> int:
    """从环境变量读取整数。"""
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _get_str(key: str, default: str = "") -> str:
    """从环境变量读取字符串。"""
    return os.environ.get(key, default)


def _parse_mcp_servers(env_value: str) -> dict:
    """解析 MCP 服务器配置。

    环境变量格式: server1=path1,server2=path2
    或者: {"server1": {"command": "...", "args": [...]}}
    """
    if not env_value:
        return {}

    # 尝试解析 JSON 格式
    if env_value.startswith("{"):
        import json
        try:
            return json.loads(env_value)
        except json.JSONDecodeError:
            pass

    # 解析简单格式: server1=path1,server2=path2
    result = {}
    for item in env_value.split(","):
        if "=" in item:
            name, path = item.split("=", 1)
            result[name.strip()] = {"command": path.strip()}
    return result


@dataclass
class RednoteConfig:
    """RedNote 内容生成服务配置。"""

    # 服务地址
    service_url: str = field(default_factory=lambda: _get_str("REDNOTE_SERVICE_URL"))
    # 认证 Token（可选）
    auth_token: str = field(default_factory=lambda: _get_str("REDNOTE_AUTH_TOKEN"))
    # 是否启用
    enabled: bool = field(default_factory=lambda: _get_bool("REDNOTE_ENABLED", False))
    # 请求超时（秒）
    timeout: int = field(default_factory=lambda: _get_int("REDNOTE_TIMEOUT", 60))

    def is_available(self) -> bool:
        """检查服务是否可用（已启用且配置了服务地址）。"""
        return self.enabled and bool(self.service_url)


@dataclass
class AgentBackendConfig:
    """Agent 后端配置。

    支持配置化选择 Agent 后端类型（native/nanobot/nanoclaw），
    并支持模块级别的后端覆盖。
    """

    # 后端类型: "native" | "nanobot" | "nanoclaw"
    backend_type: str = field(
        default_factory=lambda: _get_str("XHS_AGENT_BACKEND_TYPE", "nanobot")
    )

    # nanobot 配置
    nanobot_model: str = field(
        default_factory=lambda: _get_str("XHS_NANOBOT_MODEL", "anthropic/claude-sonnet-4-20250514")
    )
    nanobot_api_key: str = field(
        default_factory=lambda: _get_str("XHS_NANOBOT_API_KEY") or _get_str("ANTHROPIC_API_KEY") or _get_str("OPENAI_API_KEY")
    )
    nanobot_api_base: str = field(
        default_factory=lambda: _get_str("XHS_NANOBOT_API_BASE")
    )
    nanobot_max_iterations: int = field(
        default_factory=lambda: _get_int("XHS_NANOBOT_MAX_ITERATIONS", 40)
    )
    nanobot_workspace: str = field(
        default_factory=lambda: _get_str("XHS_NANOBOT_WORKSPACE", "./data/nanobot_workspace")
    )
    nanobot_context_window_tokens: int = field(
        default_factory=lambda: _get_int("XHS_NANOBOT_CONTEXT_WINDOW_TOKENS", 65536)
    )
    nanobot_web_search_enabled: bool = field(
        default_factory=lambda: _get_bool("XHS_NANOBOT_WEB_SEARCH_ENABLED", False)
    )
    nanobot_web_proxy: str = field(
        default_factory=lambda: _get_str("XHS_NANOBOT_WEB_PROXY")
    )
    nanobot_mcp_servers: dict = field(
        default_factory=lambda: _parse_mcp_servers(_get_str("XHS_NANOBOT_MCP_SERVERS"))
    )

    # 模块级后端覆盖（可选，None 表示使用全局 backend_type）
    intent_backend: str | None = field(
        default_factory=lambda: _get_str("XHS_INTENT_BACKEND") or None
    )
    planner_backend: str | None = field(
        default_factory=lambda: _get_str("XHS_PLANNER_BACKEND") or None
    )
    executor_backend: str | None = field(
        default_factory=lambda: _get_str("XHS_EXECUTOR_BACKEND") or None
    )

    def get_effective_backend(self, module: str) -> str:
        """获取模块的有效后端类型。

        Args:
            module: 模块名称（intent/planner/executor）

        Returns:
            str: 该模块应使用的后端类型
        """
        override_map = {
            "intent": self.intent_backend,
            "planner": self.planner_backend,
            "executor": self.executor_backend,
        }
        override = override_map.get(module)
        return override if override else self.backend_type

    def is_native(self) -> bool:
        """是否使用 native 后端。"""
        return self.backend_type == "native"

    def is_nanobot(self) -> bool:
        """是否使用 nanobot 后端。"""
        return self.backend_type == "nanobot"

    def is_nanoclaw(self) -> bool:
        """是否使用 nanoclaw 后端。"""
        return self.backend_type == "nanoclaw"

    def get_workspace_path(self) -> Path:
        """获取 nanobot 工作目录 Path 对象。"""
        return Path(self.nanobot_workspace)


@dataclass
class Config:
    """运行时配置；支持环境变量或配置文件。"""

    # RedNote 服务配置
    rednote: RednoteConfig = field(default_factory=RednoteConfig)

    # Agent 后端配置
    agent_backend: AgentBackendConfig = field(default_factory=AgentBackendConfig)


# 全局配置实例
config = Config()