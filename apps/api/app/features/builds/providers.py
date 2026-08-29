from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.domain import Evidence, Part, PartCategory
from app.features.builds.catalog import fixture_parts


class CatalogProvider(Protocol):
    name: str

    async def search(self, category: PartCategory, query: str = "") -> list[Part]: ...


class FixtureProvider:
    name = "fixture"

    async def search(self, category: PartCategory, query: str = "") -> list[Part]:
        items = [part for part in fixture_parts() if part.category == category]
        if query:
            lowered = query.lower()
            items = [
                part
                for part in items
                if lowered in part.name.lower() or lowered in part.brand.lower()
            ]
        return items


class OfficialMarketplaceProvider:
    """官方开放平台适配器的安全占位，不执行网页抓取。"""

    def __init__(self, name: str, credential_env: str) -> None:
        self.name = name
        self.credential_env = credential_env

    async def search(self, category: PartCategory, query: str = "") -> list[Part]:
        # 凭证和签名流程接入后再启用；无凭证时返回空结果，让上层回退 Fixture。
        return []


class EvidenceProvider(Protocol):
    async def summarize(self, title: str, url: str | None, transcript: str) -> Evidence: ...


class UserSuppliedEvidenceProvider:
    async def summarize(self, title: str, url: str | None, transcript: str) -> Evidence:
        excerpt = " ".join(transcript.split())[:500]
        return Evidence(
            source="用户提供的视频资料",
            title=title,
            url=url,
            summary=excerpt or "未提供字幕，暂不形成结论。",
            confidence="low",
        )


def fixture_captured_at() -> datetime:
    return datetime.now(UTC)
