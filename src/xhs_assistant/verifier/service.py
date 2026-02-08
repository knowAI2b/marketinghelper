"""Verifier：质量/合规/人设校验，输出 pass + 修改建议。当前占位固定返回 pass=True。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VerifierResult(BaseModel):
    """Verifier 输出：通过与否及修改建议。"""

    pass_: bool = Field(alias="pass", description="是否通过")
    suggestions: list[str] = Field(default_factory=list, description="可执行修改建议")

    model_config = {"populate_by_name": True}


class VerifierService:
    """内容评估与检验；供 replan 或 execute 后调用。"""

    def verify(self, artifact: Any, criteria: str | None = None) -> VerifierResult:
        """校验产出是否满足验收条件；占位固定返回通过。"""
        return VerifierResult(pass_=True, suggestions=[])
