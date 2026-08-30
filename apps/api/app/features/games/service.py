from __future__ import annotations

from app.config import get_settings
from app.domain import GameRequirement, GameSearchResult
from app.features.games.providers import FixtureGameProvider, SteamStoreProvider

fixture_provider = FixtureGameProvider()


async def search_games(query: str = "") -> list[GameSearchResult]:
    fixture_results = await fixture_provider.search(query)
    settings = get_settings()
    if not settings.steam_api_enabled or not query.strip():
        return fixture_results
    try:
        steam_results = await SteamStoreProvider(
            base_url=settings.steam_api_base, enabled=True
        ).search(query)
    except Exception:
        return fixture_results
    seen = {item.app_id for item in fixture_results}
    return fixture_results + [item for item in steam_results if item.app_id not in seen]


async def get_game_requirements(app_id: str) -> GameRequirement | None:
    result = await fixture_provider.get_requirements(app_id)
    if result is not None:
        return result
    settings = get_settings()
    return await SteamStoreProvider(
        base_url=settings.steam_api_base, enabled=settings.steam_api_enabled
    ).get_requirements(app_id)
