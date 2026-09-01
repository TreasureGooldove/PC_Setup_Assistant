from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.database import init_db
from app.domain import NeedProfile
from app.features.builds.service import save_plans
from app.features.conversations.service import create_conversation
from app.features.recommendations.providers import (
    MockRecommendationProvider,
    QwenRecommendationProvider,
    generate_draft,
)
from app.features.recommendations.tools import RecommendationToolRegistry
from app.llm import QwenRecommendationClient, _parse_json_content


async def _context():
    init_db()
    conversation = create_conversation(NeedProfile(budget=8000))
    plan = save_plans(conversation.id, conversation.profile)[1]
    return await RecommendationToolRegistry(conversation.profile, plan).collect()


def test_parse_json_content_accepts_fenced_json():
    assert _parse_json_content('```json\n{"headline":"ok"}\n```') == {"headline": "ok"}


@pytest.mark.asyncio
async def test_qwen_without_key_does_not_create_external_client():
    settings = Settings(_env_file=None, llm_enabled=True, llm_api_key=None)
    client = QwenRecommendationClient(settings)

    assert client.client is None
    with pytest.raises(RuntimeError, match="未配置"):
        await client.generate(await _context())


@pytest.mark.asyncio
async def test_qwen_structured_response_is_parsed_without_raw_logging():
    context = await _context()
    draft = await MockRecommendationProvider().generate(context)
    payload = json.dumps(draft.model_dump(mode="json"), ensure_ascii=False)
    settings = Settings(
        _env_file=None,
        llm_enabled=True,
        llm_api_key="test-only-key",
        llm_api_base="https://example.invalid/compatible-mode/v1",
    )
    client = QwenRecommendationClient(settings)
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=f"```json\n{payload}\n```"
                )
            )
        ]
    )
    request = AsyncMock(return_value=response)
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=request))
    )

    parsed = await client.generate(context)

    assert parsed.headline == draft.headline
    assert len(parsed.decisions) == len(context.plan_items)
    request.assert_awaited_once()


@pytest.mark.asyncio
async def test_qwen_timeout_falls_back_to_mock(monkeypatch):
    context = await _context()

    async def timeout(_: QwenRecommendationProvider, __):
        raise TimeoutError()

    monkeypatch.setattr(QwenRecommendationProvider, "generate", timeout)
    settings = Settings(
        _env_file=None,
        llm_enabled=True,
        llm_api_key="test-only-key",
        llm_api_base="https://example.invalid/compatible-mode/v1",
    )

    draft, provider, status = await generate_draft(context, settings)

    assert provider == "mock-fallback"
    assert "降级" in status
    assert len(draft.decisions) == len(context.plan_items)
