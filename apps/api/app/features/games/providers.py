from __future__ import annotations

import re
from difflib import SequenceMatcher
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
        "236390": GameRequirement(
            app_id="236390",
            name="War Thunder",
            source="Steam Store 官方配置（Fixture快照）",
            minimum=SystemRequirement(
                operating_system="Windows 10 64-bit",
                processor="双核 2.2 GHz",
                memory_gb=4,
                graphics="AMD Radeon 77XX / NVIDIA GeForce GTX 660（DirectX 11）",
                directx="DirectX 11",
                storage_gb=70,
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11 64-bit",
                processor="Intel Core i5 / AMD Ryzen 5 3600 或更高",
                memory_gb=16,
                graphics="NVIDIA GeForce GTX 1060 / AMD Radeon RX 570 或更高",
                directx="DirectX 12",
                storage_gb=95,
            ),
            notes=(
                "配置来自 Steam Store 的 Windows 系统需求快照；"
                "联网版本启用后会优先读取 appdetails。"
            ),
        ),
        "rsi:star-citizen": GameRequirement(
            app_id="rsi:star-citizen",
            name="Star Citizen（星际公民）",
            source="RSI 官方 Game and Launcher Requirements",
            source_kind="official",
            minimum=SystemRequirement(
                operating_system="Windows 10/11 64-bit",
                processor="支持 AVX/AVX2/FMA3 的四核处理器（Intel i7 Haswell+ 或 AMD Excavator+）",
                memory_gb=16,
                graphics="支持 DirectX 11.1 且显存 4GB 以上",
                directx="DirectX 11.1",
                storage_gb=150,
                additional_notes="需要 SSD；官方页面还提示应准备 NTFS 分区和系统页面文件。",
            ),
            recommended=SystemRequirement(
                operating_system="Windows 10/11 64-bit",
                processor="官方未提供统一的推荐 CPU 型号",
                memory_gb=None,
                graphics="官方未提供统一的推荐显卡型号",
                directx="未提供",
                storage_gb=150,
                additional_notes="本页主要提供最低运行要求；更高分辨率和画质应结合实际版本与测试结果评估。",
            ),
            notes=(
                "星际公民使用 RSI 官方配置入口，不伪造 Steam App ID。"
                "Linux/macOS 不是官方支持平台，社区经验仅作低可信度补充。"
            ),
        ),
    }

    _aliases = {
        "236390": ["war thunder", "warthunder", "warthuder", "战争雷霆"],
        "730": ["cs2", "counter strike 2"],
        "rsi:star-citizen": ["star citizen", "starcitizen", "星际公民", "sc"],
    }

    async def search(self, query: str) -> list[GameSearchResult]:
        lowered = query.strip().lower()
        games = [
            GameSearchResult(app_id=app_id, name=requirement.name)
            for app_id, requirement in self._games.items()
        ]
        if not lowered:
            return games
        needle = _normalise_search_text(lowered)
        matches: list[GameSearchResult] = []
        for game in games:
            candidates = [game.name, game.app_id, *self._aliases.get(game.app_id, [])]
            normalised = [_normalise_search_text(value) for value in candidates]
            if any(
                _matches_game_candidate(lowered, needle, candidate)
                for candidate in normalised
            ):
                matches.append(game)
        return matches

    async def get_requirements(self, app_id: str) -> GameRequirement | None:
        return self._games.get(app_id)


class SteamStoreProvider:
    """Steam Store appdetails 适配器；仅在显式开启时使用，不做网页抓取。"""

    name = "steam-store"

    def __init__(self, base_url: str = "https://store.steampowered.com/api", enabled: bool = False):
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled

    async def search(self, query: str) -> list[GameSearchResult]:
        if not self.enabled or not query.strip():
            return []
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.base_url}/storesearch/",
                params={"term": query.strip(), "cc": "cn", "l": "schinese"},
            )
            response.raise_for_status()
            payload = response.json()
        return [
            GameSearchResult(
                app_id=str(item.get("id", "")),
                name=str(item.get("name", "Steam 游戏")),
                source="Steam Store 搜索",
            )
            for item in payload.get("items", [])[:10]
            if str(item.get("id", "")).isdigit()
        ]

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
            source_kind="steam",
            minimum=minimum,
            recommended=recommended,
            notes="字段由 Steam Store 页面信息标准化，缺失字段保留为未提供。",
        )


def _parse_requirement_html(value: str) -> SystemRequirement:
    with_breaks = re.sub(r"<\s*(?:br|/li|/p)\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = unescape(re.sub(r"<[^>]+>", " ", with_breaks))
    lines = [re.sub(r"\s+", " ", line).strip(" -•") for line in text.splitlines()]
    lines = [line for line in lines if line]
    fields: dict[str, str] = {}
    unknown: list[str] = []
    labels = {
        "os": "operating_system",
        "operating system": "operating_system",
        "操作系统": "operating_system",
        "processor": "processor",
        "cpu": "processor",
        "处理器": "processor",
        "memory": "memory",
        "内存": "memory",
        "graphics": "graphics",
        "video card": "graphics",
        "显卡": "graphics",
        "directx": "directx",
        "storage": "storage",
        "hard drive": "storage",
        "存储空间": "storage",
    }
    for line in lines:
        match = re.match(r"^([^:：]{1,30})[:：]\s*(.+)$", line)
        if not match:
            unknown.append(line)
            continue
        key = labels.get(match.group(1).strip().lower())
        if key:
            fields[key] = match.group(2).strip()
        else:
            unknown.append(line)

    memory_match = re.search(r"(\d+)\s*GB", fields.get("memory", ""), re.IGNORECASE)
    storage_match = re.search(r"(\d+)\s*GB", fields.get("storage", ""), re.IGNORECASE)
    if not fields:
        return SystemRequirement(
            additional_notes=" ".join(lines) or "Steam 未提供该档位的完整信息。"
        )
    return SystemRequirement(
        operating_system=fields.get("operating_system", "未提供"),
        processor=fields.get("processor", "未提供"),
        memory_gb=int(memory_match.group(1)) if memory_match else None,
        graphics=fields.get("graphics", "未提供"),
        directx=fields.get("directx"),
        storage_gb=int(storage_match.group(1)) if storage_match else None,
        additional_notes="；".join(unknown) or None,
    )


def _normalise_search_text(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower())


def _matches_game_candidate(query: str, needle: str, candidate: str) -> bool:
    if len(candidate) <= 2 and candidate.isascii():
        return bool(re.search(rf"(?<![0-9a-z]){re.escape(candidate)}(?![0-9a-z])", query))
    return (
        needle in candidate
        or candidate in needle
        or SequenceMatcher(None, needle, candidate).ratio() >= 0.78
    )
