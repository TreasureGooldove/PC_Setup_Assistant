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


def test_fixture_game_provider_supports_war_thunder_and_common_typo():
    provider = FixtureGameProvider()

    exact = asyncio.run(provider.search("War Thunder"))
    typo = asyncio.run(provider.search("warthuder"))

    assert [item.app_id for item in exact] == ["236390"]
    assert [item.app_id for item in typo] == ["236390"]
    requirements = asyncio.run(provider.get_requirements("236390"))
    assert requirements is not None
    assert requirements.minimum.memory_gb == 4
    assert requirements.recommended.graphics != "未提供"


def test_steam_provider_stays_disabled_without_external_request():
    provider = SteamStoreProvider(enabled=False)

    assert asyncio.run(provider.get_requirements("730")) is None


def test_requirement_parser_preserves_unstructured_fields():
    result = _parse_requirement_html("<strong>OS:</strong> Windows 10<br>16 GB RAM")

    assert result.operating_system == "Windows 10"
    assert "16 GB RAM" in (result.additional_notes or "")


def test_requirement_parser_extracts_structured_steam_fields():
    result = _parse_requirement_html(
        "<strong>OS:</strong> Windows 10 64-bit<br>"
        "<strong>Processor:</strong> Intel Core i5<br>"
        "<strong>Memory:</strong> 16 GB RAM<br>"
        "<strong>Graphics:</strong> NVIDIA GTX 1060<br>"
        "<strong>DirectX:</strong> Version 11<br>"
        "<strong>Storage:</strong> 95 GB available space"
    )

    assert result.operating_system == "Windows 10 64-bit"
    assert result.processor == "Intel Core i5"
    assert result.memory_gb == 16
    assert result.graphics == "NVIDIA GTX 1060"
    assert result.directx == "Version 11"
    assert result.storage_gb == 95
