from __future__ import annotations

from typing import Protocol

from app.config import Settings
from app.domain import PartCategory, RecommendationDecision
from app.llm import QwenRecommendationClient

from .schemas import RecommendationContext, RecommendationDraft


class RecommendationProvider(Protocol):
    name: str

    async def generate(self, context: RecommendationContext) -> RecommendationDraft:
        ...


class MockRecommendationProvider:
    name = "mock"

    async def generate(self, context: RecommendationContext) -> RecommendationDraft:
        game_note = f"，已参考 {context.game.name} 的配置要求" if context.game else ""
        decisions: list[RecommendationDecision] = []
        for item in context.plan_items:
            slot = PartCategory(str(item["slot"]))
            reason = str(item.get("reason") or "按预算、用途和兼容性选择")
            decisions.append(
                RecommendationDecision(
                    slot=slot,
                    part_id=str(item["part_id"]),
                    part_name=str(item["name"]),
                    reason=reason,
                    evidence_ids=[f"part:{slot.value}", "compatibility", "price"],
                )
            )
        uncertainties: list[str] = []
        if not any(
            offer.get("is_live") and offer.get("price") is not None
            for item in context.price_evidence
            for offer in item.get("offers", [])
        ):
            uncertainties.append("当前金额是目录或公开参考价，购买前请核对具体店铺、规格和优惠。")
        if context.compatibility:
            uncertainties.append("兼容性检查中存在需要关注的提示，请按检查项逐一确认。")
        if context.community_evidence:
            uncertainties.append("贴吧内容来自社区讨论，仅作经验参考，不能替代官方配置和硬件参数。")
        elif context.community_query and context.community_status in {
            "disabled",
            "empty",
            "unavailable",
        }:
            uncertainties.append(
                context.community_note or "社区资料未取得，不影响确定性的装机建议。"
            )
        next_actions = ["优先核对显卡、主板和电源的具体商品规格。", "确认显示器接口与目标分辨率。"]
        return RecommendationDraft(
            headline=f"这套配置适合你的{context.need.use_case}{game_note}",
            summary=(
                f"预算约 {context.need.budget:,} 元，当前方案以 {context.need.resolution}/"
                f"{context.need.refresh_rate}Hz 为目标，建议按下列依据确认每个部件。"
            ),
            profile_summary=(
                f"{context.need.use_case} · "
                f"{context.need.resolution}/{context.need.refresh_rate}Hz · "
                f"{context.need.cooling} 散热 · {context.need.form_factor} 机身"
            ),
            decisions=decisions,
            uncertainties=uncertainties,
            next_actions=next_actions,
        )


class QwenRecommendationProvider:
    name = "qwen"

    def __init__(self, settings: Settings) -> None:
        self.client = QwenRecommendationClient(settings)

    async def generate(self, context: RecommendationContext) -> RecommendationDraft:
        return await self.client.generate(context)


async def generate_draft(
    context: RecommendationContext, settings: Settings
) -> tuple[RecommendationDraft, str, str]:
    """优先 Qwen，失败时返回可重复的本地建议，不把异常内容展示给用户。"""

    mock = MockRecommendationProvider()
    if not (settings.llm_enabled and settings.llm_api_key):
        return await mock.generate(context), mock.name, "本地演示建议（未启用外部模型）"
    try:
        draft = await QwenRecommendationProvider(settings).generate(context)
        return draft, "qwen", f"{settings.llm_model} 结构化建议"
    except Exception:
        return (
            await mock.generate(context),
            "mock-fallback",
            "Qwen 暂不可用，已降级为本地结构化建议",
        )
