from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain import (
    AgentStage,
    AgentTrace,
    BuildPlan,
    CommunityEvidence,
    CompatibilityIssue,
    GameRequirement,
    NeedProfile,
    Recommendation,
    RecommendationCompatibilitySummary,
    RecommendationDecision,
    RecommendationEvidence,
    RecommendationPriceSummary,
)

COMPATIBILITY_CHECK_COUNT = 10


class RecommendationDraft(BaseModel):
    """模型可以填写的内容；金额、兼容性和配件身份由服务端补齐。"""

    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=600)
    profile_summary: str = Field(min_length=1, max_length=500)
    decisions: list[RecommendationDecision] = Field(min_length=1, max_length=12)
    uncertainties: list[str] = Field(default_factory=list, max_length=12)
    next_actions: list[str] = Field(default_factory=list, max_length=12)


class RecommendationContext(BaseModel):
    """投给模型的最小、可审计上下文，不包含密钥、日志或隐藏思维链。"""

    model_config = ConfigDict(extra="forbid")

    version: str = "recommendation-context-v1"
    plan_id: str
    plan_fingerprint: str = Field(min_length=64, max_length=64)
    need: NeedProfile
    game: GameRequirement | None = None
    plan_items: list[dict[str, Any]] = Field(min_length=1, max_length=12)
    compatibility: list[CompatibilityIssue] = Field(default_factory=list, max_length=20)
    price_evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=24)
    evidence: list[RecommendationEvidence] = Field(default_factory=list, max_length=24)
    community_query: str | None = Field(default=None, max_length=180)
    community_status: str = Field(default="disabled", max_length=30)
    community_note: str = Field(default="", max_length=300)
    community_evidence: list[CommunityEvidence] = Field(default_factory=list, max_length=8)


class RecommendationValidationError(ValueError):
    """模型草稿不能通过确定性复核时抛出。"""


def plan_fingerprint(plan: BuildPlan) -> str:
    payload = json.dumps(
        plan.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _compatibility_summary(
    issues: list[CompatibilityIssue],
) -> RecommendationCompatibilitySummary:
    errors = [issue.detail for issue in issues if issue.severity == "error"]
    warnings = [issue.detail for issue in issues if issue.severity != "error"]
    status: Literal["ok", "warning", "error"] = (
        "error" if errors else "warning" if warnings else "ok"
    )
    return RecommendationCompatibilitySummary(
        status=status,
        passed_checks=max(0, COMPATIBILITY_CHECK_COUNT - len(issues)),
        warnings=warnings[:12],
        errors=errors[:12],
    )


def _unique_notes(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return result[:12]


def _agent_trace(
    context: RecommendationContext,
    draft: RecommendationDraft,
    provider: str,
    source_status: str,
) -> AgentTrace:
    """构造用户可核对的阶段摘要，不记录隐藏推理或原始工具日志。"""

    game_stage = (
        f"已载入 {context.game.name} 的{context.game.source_kind}配置资料。"
        if context.game
        else "未指定或未取得游戏配置，保留通用装机判断。"
    )
    if context.community_evidence:
        community_stage = (
            f"已取得 {len(context.community_evidence)} 条社区公开摘要，标记为低可信度。"
        )
    else:
        community_stage = context.community_note or "未取得社区摘要，不影响硬件规则复核。"
    game_sources = [context.game.source] if context.game else []
    research_sources = game_sources + [
        "百度贴吧社区搜索" if context.community_query else "未启用社区来源"
    ]
    live_offer_count = sum(
        1
        for item in context.price_evidence
        for offer in item.get("offers", [])
        if offer.get("is_live") and offer.get("price") is not None
    )
    compatibility_summary = (
        "未发现硬性冲突。"
        if not context.compatibility
        else f"发现 {len(context.compatibility)} 项需要关注的兼容性或资料完整性提示。"
    )
    mode: Literal["offline", "live", "fallback"] = (
        "live" if provider == "qwen" else "fallback" if "fallback" in provider else "offline"
    )
    return AgentTrace(
        stages=[
            AgentStage(
                id="need",
                label="需求识别",
                status="completed",
                summary=(
                    f"预算 {context.need.budget:,} 元，{context.need.use_case}，"
                    f"目标 {context.need.resolution}/{context.need.refresh_rate}Hz。"
                ),
                sources=["用户输入"],
            ),
            AgentStage(
                id="research",
                label="游戏与资料",
                status="completed" if context.game or context.community_evidence else "waiting",
                summary=f"{game_stage} {community_stage}",
                sources=research_sources[:8],
            ),
            AgentStage(
                id="candidates",
                label="候选与价格",
                status="completed",
                summary=(
                    f"整理 {len(context.plan_items)} 个配置项，"
                    f"已取得 {live_offer_count} 条可核验实时报价。"
                ),
                sources=["当前方案", "报价状态"],
            ),
            AgentStage(
                id="compatibility",
                label="兼容性复核",
                status="completed",
                summary=compatibility_summary,
                sources=["确定性兼容性规则"],
            ),
            AgentStage(
                id="result",
                label="生成结论",
                status="completed",
                summary=f"{source_status}；建议结果已通过服务端字段复核。",
                sources=[provider],
            ),
        ],
        result_summary=draft.summary,
        provider=provider,
        mode=mode,
        generated_at=datetime.now(UTC),
    )


def _price_summary(plan: BuildPlan, profile: NeedProfile) -> RecommendationPriceSummary:
    live_offers = [
        offer
        for item in plan.items
        for offer in item.offers
        if offer.price is not None and offer.is_live
    ]
    difference = round(plan.total_price - profile.budget, 2)
    source_notes = _unique_notes(
        [
            *(f"{item.part.name}：{item.part.source}" for item in plan.items),
            *(f"{offer.platform}：{offer.source}" for offer in live_offers),
        ]
    )
    if not live_offers:
        status: Literal["within_budget", "over_budget", "reference_only"] = "reference_only"
        source_notes.insert(0, "当前金额为目录/公开参考价，未取得可核验实时成交价")
    else:
        status = "over_budget" if difference > 0 else "within_budget"
    if difference > 0:
        source_notes.append(f"参考总价超出预算约 {difference:.0f} 元")
    return RecommendationPriceSummary(
        budget=profile.budget,
        total_price=plan.total_price,
        difference=difference,
        status=status,
        source_notes=_unique_notes(source_notes),
    )


def validate_and_build_recommendation(
    draft: RecommendationDraft,
    context: RecommendationContext,
    plan: BuildPlan,
    provider: str,
    source_status: str,
) -> Recommendation:
    """复核模型只能解释当前方案，不能改写配件、金额或兼容性事实。"""

    expected_fingerprint = plan_fingerprint(plan)
    if context.plan_id != plan.id or context.plan_fingerprint != expected_fingerprint:
        raise RecommendationValidationError("建议上下文与当前方案不一致")

    items_by_slot = {item.slot.value: item for item in plan.items}
    seen_slots: set[str] = set()
    known_evidence = {item.id for item in context.evidence}
    decisions: list[RecommendationDecision] = []
    for decision in draft.decisions:
        slot = decision.slot.value
        if slot in seen_slots:
            raise RecommendationValidationError("模型重复解释同一个配置项")
        if slot not in items_by_slot:
            raise RecommendationValidationError("模型引用了当前方案之外的配置项")
        unknown_evidence = set(decision.evidence_ids) - known_evidence
        if unknown_evidence:
            raise RecommendationValidationError("模型引用了不存在的依据")
        item = items_by_slot[slot]
        if decision.part_id != item.part.id:
            raise RecommendationValidationError("模型引用的配件不属于当前方案")
        decisions.append(
            decision.model_copy(
                update={"part_id": item.part.id, "part_name": item.part.name}
            )
        )
        seen_slots.add(slot)
    if seen_slots != set(items_by_slot):
        raise RecommendationValidationError("模型没有覆盖当前方案的全部配置项")

    return Recommendation(
        id=str(uuid4()),
        plan_id=plan.id,
        plan_fingerprint=expected_fingerprint,
        headline=draft.headline,
        summary=draft.summary,
        profile_summary=draft.profile_summary,
        decisions=decisions,
        compatibility_summary=_compatibility_summary(plan.compatibility),
        price_summary=_price_summary(plan, context.need),
        evidence=context.evidence,
        uncertainties=draft.uncertainties,
        next_actions=draft.next_actions,
        agent_trace=_agent_trace(context, draft, provider, source_status),
        provider=provider,
        source_status=source_status,
        generated_at=datetime.now(UTC),
        stale=False,
    )
