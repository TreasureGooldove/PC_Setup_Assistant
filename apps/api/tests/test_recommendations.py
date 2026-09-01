from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.domain import NeedProfile, RecommendationDecision
from app.features.builds.service import save_plans
from app.features.conversations.service import create_conversation
from app.features.jobs.service import process_one
from app.features.recommendations.providers import MockRecommendationProvider
from app.features.recommendations.schemas import (
    RecommendationValidationError,
    validate_and_build_recommendation,
)
from app.features.recommendations.service import (
    generate_recommendation,
    get_recommendation,
)
from app.features.recommendations.tools import (
    RecommendationToolError,
    RecommendationToolRegistry,
)
from app.main import app


def _saved_plan(budget: int = 8000):
    init_db()
    conversation = create_conversation(NeedProfile(budget=budget))
    return conversation, save_plans(conversation.id, conversation.profile)[1]


@pytest.mark.asyncio
async def test_recommendation_context_is_whitelisted_and_includes_game_evidence():
    conversation, plan = _saved_plan()
    registry = RecommendationToolRegistry(conversation.profile, plan, "236390")
    context = await registry.collect()

    assert context.game is not None
    assert context.game.name == "War Thunder"
    assert {item.id for item in context.evidence} >= {
        "need-profile",
        "compatibility",
        "price",
        "game-requirements",
    }
    with pytest.raises(RecommendationToolError):
        registry.call("read_raw_model_response")


@pytest.mark.asyncio
async def test_game_lookup_failure_keeps_recommendation_available():
    _, plan = _saved_plan()

    async def failing_loader(_: str):
        raise RuntimeError("external game source unavailable")

    context = await RecommendationToolRegistry(
        NeedProfile(budget=8000), plan, "999999", failing_loader
    ).collect()

    assert context.game is None
    game_evidence = next(item for item in context.evidence if item.id == "game-requirements")
    assert game_evidence.confidence == "low"
    assert "不影响硬件兼容性判断" in game_evidence.summary


@pytest.mark.asyncio
async def test_mock_recommendation_is_structured_and_round_trips():
    _, plan = _saved_plan()
    recommendation = await generate_recommendation(plan.id, "236390")
    restored = get_recommendation(recommendation.id)

    assert recommendation.provider == "mock"
    assert recommendation.price_summary.status == "reference_only"
    assert len(recommendation.decisions) == len(plan.items)
    assert {decision.part_id for decision in recommendation.decisions} == {
        item.part.id for item in plan.items
    }
    assert any(item.id == "game-requirements" for item in recommendation.evidence)
    assert restored.stale is False


@pytest.mark.asyncio
async def test_recommendation_validation_rejects_unknown_part_id():
    conversation, plan = _saved_plan()
    from app.features.recommendations.tools import RecommendationToolRegistry

    context = await RecommendationToolRegistry(conversation.profile, plan).collect()
    draft = await MockRecommendationProvider().generate(context)
    first = draft.decisions[0]
    invalid = draft.model_copy(
        update={
            "decisions": [
                RecommendationDecision(
                    slot=first.slot,
                    part_id="outside-plan",
                    part_name=first.part_name,
                    reason=first.reason,
                    evidence_ids=first.evidence_ids,
                ),
                *draft.decisions[1:],
            ]
        }
    )
    with pytest.raises(RecommendationValidationError, match="当前方案"):
        validate_and_build_recommendation(invalid, context, plan, "mock", "本地建议")


def test_recommendation_job_api_flow():
    _, plan = _saved_plan()
    with TestClient(app) as client:
        response = client.post(
            f"/api/plans/{plan.id}/recommendations",
            json={"game_app_id": "236390"},
            headers={"Idempotency-Key": f"recommendation-test-{uuid4()}"},
        )
        assert response.status_code == 202
        job = response.json()
        assert job["kind"] == "generate_recommendation"

        for _ in range(12):
            assert asyncio.run(process_one()) is True
            if client.get(f"/api/jobs/{job['id']}").json()["status"] == "completed":
                break
        finished = client.get(f"/api/jobs/{job['id']}").json()
        assert finished["status"] == "completed"
        recommendation_id = finished["result"]["recommendation_id"]
        result = client.get(f"/api/recommendations/{recommendation_id}")
        assert result.status_code == 200
        assert result.json()["plan_id"] == plan.id
        assert result.json()["evidence"]
