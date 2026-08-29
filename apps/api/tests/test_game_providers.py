import asyncio

from app.features.games.providers import (
    FixtureGameProvider,
    SteamStoreProvider,
    _parse_requirement_html,
)


def test_fixture_game_provider_supports_name_and_app_id_search():
    provider = FixtureGameProvider()

    results = asyncio.run(provider.search("Counter-Strike"))

    assert [item.app_id for item in results] == ["730"]
    assert asyncio.run(provider.get_requirements("730")).minimum.memory_gb == 8


def test_steam_provider_stays_disabled_without_external_request():
    provider = SteamStoreProvider(enabled=False)

    assert asyncio.run(provider.get_requirements("730")) is None


def test_requirement_parser_preserves_unstructured_fields():
    result = _parse_requirement_html("<strong>OS:</strong> Windows 10<br>16 GB RAM")

    assert result.operating_system == "未提供"
    assert "Windows 10" in (result.additional_notes or "")
