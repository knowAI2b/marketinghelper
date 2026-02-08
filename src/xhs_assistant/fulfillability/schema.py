"""可执行性检查输出，与 意图识别与Planner示例.md 示例五一致。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class FulfillabilityResult(BaseModel):
    """需求合理且明确但因法规/技术/成本不能执行时的返回。"""

    can_fulfill: bool = Field(description="是否可执行")
    reason: str | None = Field(default=None, description="regulation | capability | cost")
    reason_detail: str | None = Field(default=None, description="原因说明")
    message_to_user: str | None = Field(default=None, description="面向用户的说明")
    alternative: str | None = Field(default=None, description="替代方案")
    transfer_to_human: bool = Field(default=False, description="是否转人工")
    blocked_step: str | None = Field(default=None, description="被拦截的步骤名")
