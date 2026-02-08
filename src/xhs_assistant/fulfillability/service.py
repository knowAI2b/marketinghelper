"""可执行性检查：法规/技术/成本。当前占位默认 can_fulfill=True。"""
from __future__ import annotations

from xhs_assistant.fulfillability.schema import FulfillabilityResult
from xhs_assistant.intent.schema import IntentOutput


class FulfillabilityService:
    """意图后调用，不通过则不进入 Planner。"""

    def check(self, intent_output: IntentOutput, account_context: dict | None = None) -> FulfillabilityResult:
        """检查当前意图是否可执行；后续接规则或配置。"""
        account_context = account_context or {}
        # 占位：默认可执行；后续可接投流资质、API 开关、预算上限等
        if intent_output.intent_type == "ads_planning" and not account_context.get("ads_qualified"):
            return FulfillabilityResult(
                can_fulfill=False,
                reason="regulation",
                reason_detail="当前账号未完成小红书官方投流资质（报白/开户），或系统暂未接入官方投流 API。",
                message_to_user="您的投流需求已理解。因平台合规要求，当前账号需先完成小红书官方投流资质开通。",
                alternative="您可先使用「选题策划」或「内容生成」产出更多笔记，待投流能力开通后再投流。",
                transfer_to_human=True,
                blocked_step="投流",
            )
        return FulfillabilityResult(can_fulfill=True)
