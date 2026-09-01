from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import CommunityEvidence, CommunitySearchResult, NeedProfile
from app.features.builds.service import save_plans
from app.features.community.service import search_community
from app.features.community.tieba_mcp import parse_tieba_search_result
from app.features.conversations.service import create_conversation
from app.features.games.providers import FixtureGameProvider
from app.features.recommendations.providers import MockRecommendationProvider
from app.features.recommendations.schemas import validate_and_build_recommendation
from app.features.recommendations.tools import RecommendationToolRegistry
from app.main import app


def _plan():
    conversation = create_conversation(NeedProfile(budget=8000))
    return conversation, save_plans(conversation.id, conversation.profile)[1]


def test_star_citizen_is_an_official_non_steam_requirement():
    provider = FixtureGameProvider()

    results = asyncio.run(provider.search("想玩星际公民"))
    short_alias_results = asyncio.run(provider.search("SC"))
    requirement = asyncio.run(provider.get_requirements("rsi:star-citizen"))

    assert [item.app_id for item in results] == ["rsi:star-citizen"]
    assert [item.app_id for item in short_alias_results] == ["rsi:star-citizen"]
    assert requirement is not None
    assert requirement.source_kind == "official"
    assert requirement.minimum.memory_gb == 16
    assert requirement.recommended.memory_gb is None


def test_tieba_result_keeps_only_short_public_https_entries():
    result = SimpleNamespace(
        is_error=False,
        structured_content=None,
        content=[
            SimpleNamespace(
                type="text",
                text=json.dumps(
                    {
                        "results": [
                            {
                                "title": "星际公民配置讨论",
                                "description": "社区经验，仅供核对。" * 20,
                                "url": "https://tieba.baidu.com/p/123456",
                                "author": "tester",
                                "date": "2026-09-01",
                            },
                            {"title": "外部页面", "url": "https://example.com/post"},
                            {"title": "不安全链接", "url": "http://tieba.baidu.com/p/2"},
                        ]
                    },
                    ensure_ascii=False,
                ),
            )
        ],
    )

    entries = parse_tieba_search_result(result)

    assert len(entries) == 1
    assert entries[0].url == "https://tieba.baidu.com/p/123456"
    assert len(entries[0].summary) <= 400
    assert entries[0].confidence == "low"


def test_modelscope_environment_filters_auth_fields():
    settings = Settings(
        _env_file=None,
        modelscope_mcp_env_json=json.dumps(
            {
                "MODE": "stdio",
                "ALLOWED_SEARCH_ENGINES": "baidu,bing",
                "API_KEY": "should-not-pass",
                "COOKIE": "should-not-pass",
            }
        ),
    )

    assert settings.modelscope_mcp_env == {
        "MODE": "stdio",
        "ALLOWED_SEARCH_ENGINES": "baidu,bing",
    }


def test_modelscope_environment_falls_back_to_stdio_for_invalid_config():
    settings = Settings(_env_file=None, modelscope_mcp_env_json="not-json")

    assert settings.modelscope_mcp_env["MODE"] == "stdio"
    assert settings.modelscope_mcp_env["ALLOWED_SEARCH_ENGINES"] == "baidu,bing"


def test_community_search_degrades_when_mcp_is_disabled():
    settings = Settings(_env_file=None, modelscope_mcp_enabled=False)

    result = asyncio.run(search_community("星际公民 电脑配置", settings))

    assert result.status == "disabled"
    assert result.items == []
    assert result.search_url and result.search_url.startswith("https://tieba.baidu.com/")


async def _community_loader(_: str) -> CommunitySearchResult:
    return CommunitySearchResult(
        query="星际公民 电脑配置",
        status="live",
        provider="测试社区 MCP",
        note="已取得 1 条社区公开摘要。",
        items=[
            CommunityEvidence(
                id="tieba:test",
                title="星际公民配置讨论",
                summary="社区建议准备更大的内存和 SSD。",
                url="https://tieba.baidu.com/p/123456",
                source="百度贴吧（测试）",
            )
        ],
    )


def test_community_evidence_enters_agent_context_without_changing_hardware_facts():
    conversation, plan = _plan()
    registry = RecommendationToolRegistry(
        conversation.profile,
        plan,
        community_query="星际公民 电脑配置",
        community_loader=_community_loader,
    )

    context = asyncio.run(registry.collect())
    draft = asyncio.run(MockRecommendationProvider().generate(context))
    recommendation = validate_and_build_recommendation(
        draft,
        context,
        plan,
        provider="mock",
        source_status="本地测试建议",
    )

    assert len(context.community_evidence) == 1
    assert any(item.kind == "community" for item in context.evidence)
    assert recommendation.price_summary.total_price == plan.total_price
    assert recommendation.agent_trace.mode == "offline"
    research = next(stage for stage in recommendation.agent_trace.stages if stage.id == "research")
    assert research.status == "completed"
    assert "百度贴吧社区搜索" in research.sources


def test_community_and_star_citizen_routes_are_visible():
    with TestClient(app) as client:
        games = client.get("/api/games/search", params={"query": "星际公民"})
        requirements = client.get("/api/games/rsi:star-citizen/requirements")
        community = client.get("/api/community/search", params={"query": "星际公民 电脑配置"})

    assert games.status_code == 200
    assert games.json()["items"][0]["app_id"] == "rsi:star-citizen"
    assert requirements.status_code == 200
    assert requirements.json()["source_kind"] == "official"
    assert community.status_code == 200
    assert community.json()["status"] == "disabled"
