"""RedNote 内容生成服务客户端。

提供对 RedNote Flask 服务的 HTTP 调用封装。
调用条件：服务已启用且配置了有效地址。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import requests

from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


class RednoteServiceError(Exception):
    """RedNote 服务调用错误。"""
    pass


@dataclass
class ChatResult:
    """对话结果。"""
    response: str
    raw_response: str
    images: list[str] = field(default_factory=list)


class RednoteClient:
    """RedNote 内容生成服务客户端。

    使用条件：
    1. config.rednote.enabled = True
    2. config.rednote.service_url 已配置

    示例:
        client = RednoteClient()
        if client.is_available():
            result = client.chat("user_123", "帮我写一篇咖啡笔记")
            print(result.response)
    """

    def __init__(self, base_url: str | None = None, auth_token: str | None = None, timeout: int | None = None):
        """初始化客户端。

        Args:
            base_url: 服务地址，默认从配置读取
            auth_token: 认证 Token，默认从配置读取
            timeout: 请求超时（秒），默认从配置读取
        """
        self._base_url = base_url or config.rednote.service_url
        self._auth_token = auth_token or config.rednote.auth_token
        self._timeout = timeout or config.rednote.timeout

    def is_available(self) -> bool:
        """检查服务是否可用。"""
        return bool(self._base_url) and config.rednote.enabled

    def _get_headers(self) -> dict[str, str]:
        """获取请求头。"""
        headers = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """处理响应。"""
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise RednoteServiceError(f"响应解析失败: {e}") from e

        if response.status_code != 200:
            msg = data.get("message", f"HTTP {response.status_code}")
            raise RednoteServiceError(msg)

        return data

    def chat(
        self,
        session_id: str,
        message: str,
        clear_history: bool = False,
    ) -> ChatResult:
        """发送对话请求。

        Args:
            session_id: 用户会话 ID
            message: 用户消息
            clear_history: 是否清空历史

        Returns:
            ChatResult: 对话结果

        Raises:
            RednoteServiceError: 服务调用失败
        """
        if not self.is_available():
            raise RednoteServiceError("RedNote 服务未启用或未配置")

        url = f"{self._base_url.rstrip('/')}/chat"
        payload = {
            "session_id": session_id,
            "message": message,
            "clear_history": clear_history,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            data = self._handle_response(response)
        except requests.Timeout:
            raise RednoteServiceError(f"请求超时（{self._timeout}s）")
        except requests.ConnectionError as e:
            raise RednoteServiceError(f"连接失败: {e}")
        except requests.RequestException as e:
            raise RednoteServiceError(f"请求失败: {e}")

        result_data = data.get("data", {})
        return ChatResult(
            response=result_data.get("response", ""),
            raw_response=result_data.get("raw_response", ""),
            images=result_data.get("images", []),
        )

    def clear_history(self, session_id: str) -> bool:
        """清空对话历史。

        Args:
            session_id: 用户会话 ID

        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False

        url = f"{self._base_url.rstrip('/')}/chat/clear"
        payload = {"session_id": session_id}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            data = self._handle_response(response)
            return data.get("code") == 200
        except (RednoteServiceError, requests.RequestException) as e:
            logger.warning(f"清空历史失败: {e}")
            return False

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """获取对话历史。

        Args:
            session_id: 用户会话 ID

        Returns:
            list: 消息历史列表
        """
        if not self.is_available():
            return []

        url = f"{self._base_url.rstrip('/')}/chat/history"
        params = {"session_id": session_id}

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            data = self._handle_response(response)
            return data.get("data", {}).get("messages", [])
        except (RednoteServiceError, requests.RequestException) as e:
            logger.warning(f"获取历史失败: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """删除会话。

        Args:
            session_id: 用户会话 ID

        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False

        url = f"{self._base_url.rstrip('/')}/session/delete"
        payload = {"session_id": session_id}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            data = self._handle_response(response)
            return data.get("code") == 200
        except (RednoteServiceError, requests.RequestException) as e:
            logger.warning(f"删除会话失败: {e}")
            return False

    def health_check(self) -> bool:
        """健康检查。

        Returns:
            bool: 服务是否健康
        """
        if not self._base_url:
            return False

        try:
            # RedNote 服务没有 /health 端点，用简单的请求测试
            response = requests.get(
                f"{self._base_url.rstrip('/')}/",
                timeout=5,
            )
            return response.status_code in (200, 404)  # 404 也说明服务在运行
        except requests.RequestException:
            return False


# 全局客户端实例
_client: RednoteClient | None = None


def get_rednote_client() -> RednoteClient:
    """获取全局 RedNote 客户端实例。"""
    global _client
    if _client is None:
        _client = RednoteClient()
    return _client