from __future__ import annotations

import re
from html import unescape
from typing import Protocol

import httpx

from app.domain import GameRequirement, GameSearchResult, SystemRequirement


class GameConfigProvider(Protocol):
    name: str

    async def search(self, query: str) -> list[GameSearchResult]: ...

    async def get_requirements(self, app_id: str) -> GameRequirement | None: ...


class FixtureGameProvider:
    name = "fixture"

    _games = {
        "730": GameRequirement(
            app_id="730",
            name="Counter-Strike 2",
            minimum=SystemRequirement(
                operating_system="Windows 10",
                processor="Intel Core i5-750 或 AMD Ryzen 5 1600",
                memory_gb=8,
                graphics="NVIDIA GTX 1060 / AMD RX 580",
                directx="DirectX 11",
                storage_gb=85,
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11",
                processor="Intel Core i5-12400 或 AMD Ryzen 5 5600",
                memory_gb=16,
                graphics="NVIDIA RTX 3060 / AMD RX 6600",
                directx="DirectX 11",
                storage_gb=85,
            ),
            notes="推荐配置为本地参考整理，实际体验会随分辨率和画质设置变化。",
        ),
        "1245620": GameRequirement(
            app_id="1245620",
            name="Elden Ring",
            minimum=SystemRequirement(
                operating_system="Windows 10",
                processor="Intel Core i5-8400 或 AMD Ryzen 3 3300X",
                memory_gb=12,
                graphics="NVIDIA GTX 1060 3GB / AMD RX 580 4GB",
                directx="DirectX 12",
                storage_gb=60,
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11",
                processor="Intel Core i7-8700K 或 AMD Ryzen 5 3600X",
                memory_gb=16,
                graphics="NVIDIA GTX 1070 8GB / AMD RX Vega 56 8GB",
                directx="DirectX 12",
                storage_gb=60,
            ),
            notes="适合用 2K 目标做整机预算评估，建议为系统和更新预留额外空间。",
        ),
        "1086940": GameRequirement(
            app_id="1086940",
            name="Baldur's Gate 3",
            minimum=SystemRequirement(
                operating_system="Windows 10 64-bit",
                processor="Intel Core i5-4690 / AMD FX 8350",
                memory_gb=8,
                graphics="NVIDIA GTX 970 / AMD RX 480",
                directx="DirectX 11",
                storage_gb=150,
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11 64-bit",
                processor="Intel Core i7-8700K / AMD Ryzen 5 3600",
                memory_gb=16,
                graphics="NVIDIA RTX 2060 SUPER / AMD RX 5700 XT",
                directx="DirectX 11",
                storage_gb=150,
            ),
            notes="大型游戏建议优先确认固态硬盘剩余空间，而不只看硬盘标称容量。",
        ),
        "1172470": GameRequirement(
            app_id="1172470",
            name="Apex Legends",
            minimum=SystemRequirement(
                operating_system="Windows 10 64-bit",
                processor="Intel Core i3-6300 或同级",
                memory_gb=6,
                graphics="NVIDIA GTX 660 / AMD Radeon HD 7870",
                directx="DirectX 11",
                storage_gb=75,
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11 64-bit",
                processor="Intel Core i5-11600K 或 AMD Ryzen 5 5600X",
                memory_gb=16,
                graphics="NVIDIA RTX 3060 / AMD RX 6600 XT",
                directx="DirectX 11",
                storage_gb=75,
            ),
        ),
    }

    async def search(self, query: str) -> list[GameSearchResult]:
        lowered = query.strip().lower()
        games = [
            GameSearchResult(app_id=app_id, name=requirement.name)
            for app_id, requirement in self._games.items()
        ]
        if not lowered:
            return games
        return [game for game in games if lowered in game.name.lower() or lowered in game.app_id]

    async def get_requirements(self, app_id: str) -> GameRequirement | None:
        return self._games.get(app_id)


class SteamStoreProvider:
    """Steam Store appdetails 适配器；仅在显式开启时使用，不做网页抓取。"""

    name = "steam-store"

    def __init__(self, base_url: str = "https://store.steampowered.com/api", enabled: bool = False):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled

    async def search(self, query: str) -> list[GameSearchResult]:
        # Steam Store 的搜索接口格式和限流策略可能变化，预留为后续官方适配实现。
        return []

    async def get_requirements(self, app_id: str) -> GameRequirement | None:
        if not self.enabled or not app_id.isdigit():
            return None
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.base_url}/appdetails",
                params={"appids": app_id, "cc": "cn", "l": "schinese"},
            )
            response.raise_for_status()
            payload = response.json().get(app_id, {})
        if not payload.get("success"):
            return None
        data = payload.get("data", {})
        minimum = _parse_requirement_html(data.get("pc_requirements", {}).get("minimum", ""))
        recommended = _parse_requirement_html(
            data.get("pc_requirements", {}).get("recommended", "")
        )
        return GameRequirement(
            app_id=app_id,
            name=str(data.get("name", f"Steam 游戏 {app_id}")),
            source="Steam Store appdetails",
            minimum=minimum,
            recommended=recommended,
            notes="字段由 Steam Store 页面信息标准化，缺失字段保留为未提供。",
        )


def _parse_requirement_html(value: str) -> SystemRequirement:
    text = unescape(re.sub(r"<[^>]+>", " ", value))
    text = re.sub(r"\s+", " ", text).strip()
    return SystemRequirement(additional_notes=text or "Steam 未提供该档位的完整信息。")
