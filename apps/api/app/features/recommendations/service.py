from __future__ import annotations

from datetime import UTC, datetime

from app.config import get_settings
from app.database import RecommendationRecord, SessionLocal, json_dump, json_load
from app.domain import Recommendation
from app.errors import NotFoundError
from app.features.builds.service import get_plan, get_plan_with_conversation
from app.features.conversations.service import get_conversation

from .providers import MockRecommendationProvider, generate_draft
from .schemas import (
    RecommendationValidationError,
    plan_fingerprint,
    validate_and_build_recommendation,
)
from .tools import RecommendationToolRegistry


def save_recommendation(recommendation: Recommendation) -> Recommendation:
    now = datetime.now(UTC)
    with SessionLocal() as session:
        session.add(
            RecommendationRecord(
                id=recommendation.id,
                plan_id=recommendation.plan_id,
                plan_fingerprint=recommendation.plan_fingerprint,
                recommendation_json=json_dump(recommendation.model_dump(mode="json")),
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    return recommendation


async def generate_recommendation(
    plan_id: str,
    game_app_id: str | None = None,
    community_query: str | None = None,
    include_community_evidence: bool = True,
) -> Recommendation:
    plan, conversation_id = get_plan_with_conversation(plan_id)
    conversation = get_conversation(conversation_id)
    registry = RecommendationToolRegistry(
        conversation.profile,
        plan,
        game_app_id,
        community_query=community_query,
        include_community_evidence=include_community_evidence,
    )
    context = await registry.collect()
    draft, provider, source_status = await generate_draft(context, get_settings())
    try:
        recommendation = validate_and_build_recommendation(
            draft, context, plan, provider, source_status
        )
    except RecommendationValidationError:
        fallback = await MockRecommendationProvider().generate(context)
        recommendation = validate_and_build_recommendation(
            fallback,
            context,
            plan,
            "mock-fallback",
            "模型结果未通过校验，已降级为本地结构化建议",
        )
    return save_recommendation(recommendation)


def get_recommendation(recommendation_id: str) -> Recommendation:
    with SessionLocal() as session:
        record = session.get(RecommendationRecord, recommendation_id)
        if not record:
            raise NotFoundError("装机建议", recommendation_id)
        recommendation = Recommendation.model_validate(json_load(record.recommendation_json, {}))
    current_plan = get_plan(recommendation.plan_id)
    stale = recommendation.plan_fingerprint != plan_fingerprint(current_plan)
    return recommendation.model_copy(update={"stale": stale})
