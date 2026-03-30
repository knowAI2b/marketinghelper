"""RAG 检索服务客户端。

提供对 xhs_agent API 的 HTTP 调用封装，用于获取选题卡数据。
支持异步任务轮询和本地缓存。

调用条件：服务已启用且配置了有效地址。
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from xhs_assistant.shared.config import config

logger = logging.getLogger(__name__)


class RagServiceError(Exception):
    """RAG 服务调用错误。"""
    pass


@dataclass
class TopicCardData:
    """选题卡数据。"""
    trend_summary: str = ""
    title_hooks: list[str] = field(default_factory=list)
    recommended_tags: list[str] = field(default_factory=list)
    faq_top_questions: list[str] = field(default_factory=list)
    compliance_risks: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RagResult:
    """RAG 检索结果。"""
    job_id: str = ""
    status: str = "pending"
    topic_card: TopicCardData | None = None
    error: str | None = None

    def is_success(self) -> bool:
        """检查是否成功。"""
        return self.status == "succeeded" and self.topic_card is not None

    def is_empty(self) -> bool:
        """检查是否为空结果。"""
        return self.topic_card is None


class RagClient:
    """RAG 检索服务客户端。

    用于从 xhs_agent API 获取选题卡数据，支持：
    - 异步任务轮询
    - 本地缓存（基于产品信息 fingerprint）
    - 失败降级

    使用条件：
    1. config.rag.enabled = True
    2. config.rag.service_url 已配置

    示例:
        client = RagClient()
        if client.is_available():
            result = await client.get_topic_card_for_product("咖啡", "饮品")
            print(result.topic_card.trend_summary)
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
        cache_dir: str | None = None,
        cache_ttl_hours: int | None = None,
    ):
        """初始化客户端。

        Args:
            base_url: 服务地址，默认从配置读取
            api_key: 认证 API Key，默认从配置读取
            timeout: 请求超时（秒），默认从配置读取
            cache_dir: 缓存目录，默认从配置读取
            cache_ttl_hours: 缓存 TTL（小时），默认从配置读取
        """
        self._base_url = base_url or config.rag.service_url
        self._api_key = api_key or config.rag.api_key
        self._timeout = timeout or config.rag.timeout
        self._cache_dir = Path(cache_dir or config.rag.cache_dir)
        self._cache_ttl_hours = cache_ttl_hours or config.rag.cache_ttl_hours

    def is_available(self) -> bool:
        """检查服务是否可用。"""
        return bool(self._base_url) and config.rag.enabled

    def _get_headers(self) -> dict[str, str]:
        """获取请求头。"""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            # 支持两种认证方式
            headers["x-api-key"] = self._api_key
        return headers

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """处理响应。"""
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise RagServiceError(f"响应解析失败: {e}") from e

        # 接受 2xx 状态码（200 OK, 201 Created, 202 Accepted）
        if not (200 <= response.status_code < 300):
            msg = data.get("message") or data.get("error") or f"HTTP {response.status_code}"
            raise RagServiceError(msg)

        return data

    # =========================================================================
    # 缓存相关方法
    # =========================================================================

    def _get_cache_key(self, product: str, category: str | None = None, topic: str | None = None) -> str:
        """生成缓存键（基于产品信息的 SHA1 fingerprint）。"""
        cache_input = f"product:{product}|category:{category or ''}|topic:{topic or ''}"
        return hashlib.sha1(cache_input.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径。"""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """检查缓存是否有效（未过期）。"""
        if not cache_path.exists():
            return False

        cache_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        return cache_age_hours < self._cache_ttl_hours

    def _read_cache(self, cache_key: str) -> RagResult | None:
        """读取缓存。"""
        cache_path = self._get_cache_path(cache_key)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            topic_card_data = data.get("topic_card", {})
            return RagResult(
                job_id=data.get("job_id", ""),
                status=data.get("status", "completed"),
                topic_card=TopicCardData(
                    trend_summary=topic_card_data.get("trend_summary", ""),
                    title_hooks=topic_card_data.get("title_hooks", []),
                    recommended_tags=topic_card_data.get("recommended_tags", []),
                    faq_top_questions=topic_card_data.get("faq_top_questions", []),
                    compliance_risks=topic_card_data.get("compliance_risks", []),
                    raw_data=topic_card_data,
                ),
            )
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"读取缓存失败: {e}")
            return None

    def _write_cache(self, cache_key: str, result: RagResult) -> None:
        """写入缓存。"""
        cache_path = self._get_cache_path(cache_key)

        try:
            data = {
                "job_id": result.job_id,
                "status": result.status,
                "cached_at": time.time(),
                "topic_card": result.topic_card.raw_data if result.topic_card else {},
            }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except IOError as e:
            logger.warning(f"写入缓存失败: {e}")

    # =========================================================================
    # API 调用方法
    # =========================================================================

    def create_topic_card_job(
        self,
        product: str,
        category: str | None = None,
        topic: str | None = None,
        campaign: str | None = None,
    ) -> str:
        """创建选题卡生成任务。

        Args:
            product: 产品名称
            category: 产品类目
            topic: 话题/主题
            campaign: 营销活动目标

        Returns:
            str: 任务 ID

        Raises:
            RagServiceError: 服务调用失败
        """
        if not self.is_available():
            raise RagServiceError("RAG 服务未启用或未配置")

        # 使用正确的 API 端点
        url = f"{self._base_url.rstrip('/')}/v1/topic-cards/jobs"

        # 构建符合服务端期望的请求体格式
        payload = {
            "product_info": {
                "category": category or product,
            },
            "campaign": {
                "goal": campaign or "拉新种草",
            },
        }

        # 如果有 topic，添加到 competitors 用于生成相关查询
        if topic:
            payload["competitors"] = [topic]

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            data = self._handle_response(response)
        except requests.Timeout:
            raise RagServiceError(f"请求超时（{self._timeout}s）")
        except requests.ConnectionError as e:
            raise RagServiceError(f"连接失败: {e}")
        except requests.RequestException as e:
            raise RagServiceError(f"请求失败: {e}")

        job_id = data.get("job_id")
        if not job_id:
            raise RagServiceError("响应中缺少 job_id")

        return job_id

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """获取任务状态。

        Args:
            job_id: 任务 ID

        Returns:
            dict: 任务状态信息

        Raises:
            RagServiceError: 服务调用失败
        """
        if not self.is_available():
            raise RagServiceError("RAG 服务未启用或未配置")

        # 使用正确的 API 端点
        url = f"{self._base_url.rstrip('/')}/v1/topic-cards/jobs/{job_id}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30,  # 状态查询用较短超时
            )
            data = self._handle_response(response)
        except requests.Timeout:
            raise RagServiceError("状态查询超时")
        except requests.ConnectionError as e:
            raise RagServiceError(f"连接失败: {e}")
        except requests.RequestException as e:
            raise RagServiceError(f"请求失败: {e}")

        return data

    def wait_for_job(
        self,
        job_id: str,
        timeout: int | None = None,
        poll_interval: int = 3,
    ) -> RagResult:
        """轮询等待任务完成。

        Args:
            job_id: 任务 ID
            timeout: 总超时时间（秒），默认使用配置的 timeout
            poll_interval: 轮询间隔（秒）

        Returns:
            RagResult: 检索结果

        Raises:
            RagServiceError: 服务调用失败或超时
        """
        if timeout is None:
            timeout = self._timeout

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise RagServiceError(f"任务超时（{timeout}s）")

            try:
                status_data = self.get_job_status(job_id)
                status = status_data.get("status", "queued")

                if status == "succeeded":
                    # 任务成功，需要获取结果
                    return self._fetch_topic_card_result(job_id, status_data)

                if status == "failed":
                    error_msg = status_data.get("error_message", "未知错误")
                    return RagResult(
                        job_id=job_id,
                        status="failed",
                        error=error_msg,
                    )

                # 继续等待 (queued, running)
                logger.debug(f"任务 {job_id} 状态: {status}, 进度: {status_data.get('progress', {})}")
                time.sleep(poll_interval)

            except RagServiceError as e:
                logger.warning(f"查询任务状态失败: {e}")
                time.sleep(poll_interval)

    def _fetch_topic_card_result(self, job_id: str, status_data: dict[str, Any]) -> RagResult:
        """获取选题卡结果。

        Args:
            job_id: 任务 ID
            status_data: 任务状态数据

        Returns:
            RagResult: 检索结果
        """
        # 从结果端点获取完整数据
        url = f"{self._base_url.rstrip('/')}/v1/topic-cards/{job_id}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30,
            )
            data = self._handle_response(response)
        except (RagServiceError, requests.RequestException) as e:
            logger.warning(f"获取选题卡结果失败: {e}")
            return RagResult(
                job_id=job_id,
                status="succeeded",
                error=f"获取结果失败: {e}",
            )

        # 解析选题卡数据
        topic_card_data = data.get("topic_card", {})
        title_hooks_dict = topic_card_data.get("title_hooks", {})
        # title_hooks 是一个 dict，需要展平为 list
        title_hooks_list = []
        if isinstance(title_hooks_dict, dict):
            for hooks in title_hooks_dict.values():
                if isinstance(hooks, list):
                    title_hooks_list.extend(hooks)
        elif isinstance(title_hooks_dict, list):
            title_hooks_list = title_hooks_dict

        # 解析 FAQ 问题
        faq_data = topic_card_data.get("faq_top_questions", [])
        faq_questions = []
        if isinstance(faq_data, list):
            for item in faq_data:
                if isinstance(item, dict):
                    faq_questions.append(item.get("question", ""))
                elif isinstance(item, str):
                    faq_questions.append(item)

        return RagResult(
            job_id=job_id,
            status="succeeded",
            topic_card=TopicCardData(
                trend_summary=topic_card_data.get("trend_summary", ""),
                title_hooks=title_hooks_list,
                recommended_tags=topic_card_data.get("recommended_tags", []),
                faq_top_questions=faq_questions,
                compliance_risks=topic_card_data.get("compliance_risks", []),
                raw_data=topic_card_data,
            ),
        )

    def get_topic_card_for_product(
        self,
        product: str,
        category: str | None = None,
        topic: str | None = None,
        campaign: str | None = None,
        use_cache: bool = True,
    ) -> RagResult:
        """获取产品的选题卡数据（带缓存）。

        这是主要的对外接口，封装了缓存逻辑和 API 调用。

        Args:
            product: 产品名称
            category: 产品类目
            topic: 话题/主题
            campaign: 营销活动
            use_cache: 是否使用缓存

        Returns:
            RagResult: 检索结果（失败时返回空结果，允许降级）
        """
        # 生成缓存键
        cache_key = self._get_cache_key(product, category, topic)

        # 尝试读取缓存
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached is not None:
                logger.info(f"使用缓存的选题卡数据: {cache_key}")
                return cached

        # 检查服务是否可用
        if not self.is_available():
            logger.info("RAG 服务未启用，返回空结果")
            return RagResult(status="unavailable", error="RAG 服务未启用")

        try:
            # 创建任务
            job_id = self.create_topic_card_job(product, category, topic, campaign)
            logger.info(f"创建选题卡任务: {job_id}")

            # 等待完成
            result = self.wait_for_job(job_id)

            # 写入缓存
            if result.is_success():
                self._write_cache(cache_key, result)
                logger.info(f"选题卡数据已缓存: {cache_key}")

            return result

        except RagServiceError as e:
            logger.warning(f"获取选题卡失败: {e}，返回空结果（降级）")
            return RagResult(status="error", error=str(e))

    def health_check(self) -> bool:
        """健康检查。

        Returns:
            bool: 服务是否健康
        """
        if not self._base_url:
            return False

        try:
            # 使用正确的健康检查端点
            response = requests.get(
                f"{self._base_url.rstrip('/')}/healthz",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


# 全局客户端实例
_client: RagClient | None = None


def get_rag_client() -> RagClient:
    """获取全局 RAG 客户端实例。"""
    global _client
    if _client is None:
        _client = RagClient()
    return _client