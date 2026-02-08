"""运行时配置占位：LLM、向量库、平台开关。构建阶段不依赖真实 API Key。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """占位配置；后续可接环境变量或配置文件。"""

    # LLM：占位 URL 或模型名，避免 build 依赖真实 Key
    llm_planning_model: str = field(default_factory=lambda: os.environ.get("LLM_PLANNING_MODEL", ""))
    llm_execution_model: str = field(default_factory=lambda: os.environ.get("LLM_EXECUTION_MODEL", ""))
    # 向量库 / RAG（可选）
    vector_store_type: str = "memory"
    # 平台：是否启用投流等
    enable_ads: bool = False
