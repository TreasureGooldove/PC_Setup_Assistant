from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.domain import BuildPlan, CommunitySearchResult, GameRequirement, NeedProfile
from app.features.community.service import default_community_query, search_community
from app.features.games.service import get_game_requirements

from .schemas import RecommendationContext, RecommendationEvidence, plan_fingerprint

ALLOWED_TOOL_NAMES = frozenset(
    {
        "get_need_profile",
        "get_game_requirements",
        "get_plan_items",
        "get_compatibility_result",
        "get_price_evidence",
        "get_community_evidence",
    }
)


def _clip(value: Any, limit: int = 240) -> Any:
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_clip(item, limit) for item in value[:20]]
    if isinstance(value, dict):
        return {str(key)[:80]: _clip(item, limit) for key, item in list(value.items())[:40]}
    return str(value)[:limit]


class RecommendationToolError(ValueError):
    pass


class RecommendationToolRegistry:
    """只读上下文工具注册表；工具输出不含凭证、原始模型响应或私密日志。"""

    def __init__(
        self,
        profile: NeedProfile,
        plan: BuildPlan,
        game_app_id: str | None = None,
        game_loader: Callable[[str], Awaitable[GameRequirement | None]] = get_game_requirements,
        community_query: str | None = None,
        include_community_evidence: bool = True,
        community_loader: Callable[[str], Awaitable[CommunitySearchResult]] = search_community,
    ) -> None:
        self.profile = profile
        self.plan = plan
        self.game_app_id = game_app_id
        self.game_loader = game_loader
        self.community_query = community_query
        self.include_community_evidence = include_community_evidence
        self.community_loader = community_loader
        self.game: GameRequirement | None = None
        self.game_lookup_failed = False
        self.community_result = CommunitySearchResult(
            query="未设置",
            status="disabled",
            provider="社区来源",
            note="未启用社区来源。",
        )

    def call(self, name: str) -> dict[str, Any]:
        if name not in ALLOWED_TOOL_NAMES:
            raise RecommendationToolError(f"未允许的建议工具：{name}")
        method = getattr(self, f"_{name}", None)
        if method is None:
            raise RecommendationToolError(f"建议工具未实现：{name}")
        return cast(dict[str, Any], _clip(method()))

    async def collect(self) -> RecommendationContext:
        if self.game_app_id:
            try:
                self.game = await self.game_loader(self.game_app_id)
            except Exception:
                # 游戏配置只是辅助证据，查询失败不能阻塞确定性的装机建议。
                self.game_lookup_failed = True
                self.game = None
        if self.include_community_evidence:
            query = self.community_query or default_community_query(self.profile, self.game)
            try:
                self.community_result = await self.community_loader(query)
            except Exception as exc:
                self.community_result = CommunitySearchResult(
                    query=query,
                    status="unavailable",
                    provider="社区来源",
                    note=f"社区资料未取得：{str(exc)[:180]}",
                )
        evidence = self._evidence()
        return RecommendationContext(
            plan_id=self.plan.id,
            plan_fingerprint=plan_fingerprint(self.plan),
            need=self.profile,
            game=self.game,
            plan_items=self.call("get_plan_items")["items"],
            compatibility=self.plan.compatibility,
            price_evidence=self.call("get_price_evidence")["items"],
            evidence=evidence,
            community_query=(
                self.community_result.query if self.include_community_evidence else None
            ),
            community_status=self.community_result.status,
            community_note=self.community_result.note,
            community_evidence=self.community_result.items,
        )

    def _get_need_profile(self) -> dict[str, Any]:
        return {"profile": self.profile.model_dump(mode="json")}

    def _get_game_requirements(self) -> dict[str, Any]:
        return {
            "app_id": self.game.app_id if self.game else self.game_app_id,
            "game": self.game.model_dump(mode="json") if self.game else None,
        }

    def _get_plan_items(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan.id,
            "items": [
                {
                    "slot": item.slot.value,
                    "part_id": item.part.id,
                    "name": item.part.name,
                    "brand": item.part.brand,
                    "reference_price": item.part.price,
                    "source": item.part.source,
                    "source_url": item.part.url,
                    "power_w": item.part.power_w,
                    "reason": item.reason,
                    "specs": _clip(item.part.specs),
                }
                for item in self.plan.items
            ],
        }

    def _get_compatibility_result(self) -> dict[str, Any]:
        return {
            "rules_total": 10,
            "issues": [issue.model_dump(mode="json") for issue in self.plan.compatibility],
        }

    def _get_price_evidence(self) -> dict[str, Any]:
        return {
            "currency": "CNY",
            "total_reference_price": self.plan.total_price,
            "items": [
                {
                    "slot": item.slot.value,
                    "part_id": item.part.id,
                    "reference_price": item.part.price,
                    "part_source": item.part.source,
                    "offers": [
                        {
                            "platform": offer.platform,
                            "price": offer.price,
                            "status": offer.status,
                            "source": offer.source,
                            "seller": offer.seller,
                            "captured_at": offer.captured_at.isoformat()
                            if offer.captured_at
                            else None,
                            "is_live": offer.is_live,
                            "url": offer.url,
                        }
                        for offer in item.offers
                    ],
                }
                for item in self.plan.items
            ],
        }

    def _get_community_evidence(self) -> dict[str, Any]:
        return {
            "query": self.community_result.query,
            "status": self.community_result.status,
            "provider": self.community_result.provider,
            "note": self.community_result.note,
            "search_url": self.community_result.search_url,
            "items": [item.model_dump(mode="json") for item in self.community_result.items],
        }

    def _evidence(self) -> list[RecommendationEvidence]:
        evidence = [
            RecommendationEvidence(
                id="need-profile",
                kind="profile",
                label="需求输入",
                source="用户输入",
                summary=(
                    f"预算 {self.profile.budget:,} 元，用途为 {self.profile.use_case}，"
                    f"目标 {self.profile.resolution}/{self.profile.refresh_rate}Hz。"
                ),
                confidence="high",
            )
        ]
        for item in self.plan.items:
            evidence.append(
                RecommendationEvidence(
                    id=f"part:{item.slot.value}",
                    kind="part",
                    label=item.part.name,
                    source=item.part.source,
                    summary=(
                        f"{item.part.brand} {item.part.name}，目录参考价 {item.part.price:.0f} 元；"
                        f"{item.reason or '按预算与兼容性选择'}"
                    ),
                    url=item.part.url,
                    confidence="medium",
                )
            )
        issue_count = len(self.plan.compatibility)
        evidence.append(
            RecommendationEvidence(
                id="compatibility",
                kind="compatibility",
                label="兼容性复核",
                source="确定性兼容性规则",
                summary=(
                    "10 项装机规则均通过。"
                    if issue_count == 0
                    else f"发现 {issue_count} 项需要关注的兼容性或资料完整性提示。"
                ),
                confidence="high",
            )
        )
        live_offer_count = sum(
            1
            for item in self.plan.items
            for offer in item.offers
            if offer.price is not None and offer.is_live
        )
        evidence.append(
            RecommendationEvidence(
                id="price",
                kind="price",
                label="价格依据",
                source="公开目录与报价状态",
                summary=(
                    f"整机参考价 {self.plan.total_price:.0f} 元，"
                    f"已取得 {live_offer_count} 条可核验实时报价。"
                    if live_offer_count
                    else f"整机参考价 {self.plan.total_price:.0f} 元，当前未取得可核验实时成交价。"
                ),
                confidence="medium" if live_offer_count else "low",
            )
        )
        if self.game:
            evidence.append(
                RecommendationEvidence(
                    id="game-requirements",
                    kind="game",
                    label=f"{self.game.name} 配置要求",
                    source=self.game.source,
                    summary=(
                        f"已载入最低配置与推荐配置；最低显卡 {self.game.minimum.graphics}，"
                        f"推荐显卡 {self.game.recommended.graphics}。"
                    ),
                    confidence="medium",
                )
            )
        elif self.game_app_id and self.game_lookup_failed:
            evidence.append(
                RecommendationEvidence(
                    id="game-requirements",
                    kind="game",
                    label="游戏配置要求",
                    source="Steam 配置查询",
                    summary="本次未取得该游戏的最低/推荐配置，建议打开游戏配置入口后重试；不影响硬件兼容性判断。",
                    confidence="low",
                )
            )
        if self.include_community_evidence:
            if self.community_result.items:
                for community_item in self.community_result.items:
                    evidence.append(
                        RecommendationEvidence(
                            id=f"community:{community_item.id}",
                            kind="community",
                            label=community_item.title,
                            source=community_item.source,
                            summary=community_item.summary,
                            url=community_item.url,
                            confidence="low",
                        )
                    )
            else:
                evidence.append(
                    RecommendationEvidence(
                        id="community-status",
                        kind="community",
                        label="贴吧社区资料",
                        source=self.community_result.provider,
                        summary=self.community_result.note,
                        url=self.community_result.search_url,
                        confidence="low",
                    )
                )
        return evidence
