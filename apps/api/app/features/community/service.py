"""社区证据服务和降级入口。"""

from __future__ import annotations

from urllib.parse import quote

from app.config import Settings, get_settings
from app.domain import CommunitySearchResult, GameRequirement, NeedProfile

from .tieba_mcp import search_tieba_mcp


def default_community_query(
    profile: NeedProfile, game: GameRequirement | None = None
) -> str:
    subject = game.name if game else profile.use_case
    return f"site:tieba.baidu.com {subject} 电脑配置 CPU 显卡 内存 SSD"


def tieba_search_url(query: str) -> str:
    return f"https://tieba.baidu.com/f/search/adv?kw={quote(query, safe='')}"


async def search_community(
    query: str, settings: Settings | None = None
) -> CommunitySearchResult:
    settings = settings or get_settings()
    value = " ".join(query.split())
    if not value:
        raise ValueError("社区搜索词不能为空")
    search_url = tieba_search_url(value)
    if not settings.modelscope_mcp_enabled:
        return CommunitySearchResult(
            query=value,
            status="disabled",
            provider="ModelScope open-webSearch MCP",
            note="社区搜索未启用；可打开百度贴吧高级搜索人工核对。",
            search_url=search_url,
        )
    try:
        items = await search_tieba_mcp(value, settings)
    except Exception as exc:
        return CommunitySearchResult(
            query=value,
            status="unavailable",
            provider="ModelScope open-webSearch MCP",
            note=f"社区搜索暂不可用：{str(exc)[:180]}",
            search_url=search_url,
        )
    if not items:
        return CommunitySearchResult(
            query=value,
            status="empty",
            provider="ModelScope open-webSearch MCP",
            note="未取得可核对的贴吧帖子；可打开搜索入口人工查看。",
            search_url=search_url,
        )
    return CommunitySearchResult(
        query=value,
        status="live",
        provider="ModelScope open-webSearch MCP",
        note=f"已取得 {len(items)} 条贴吧公开摘要，仅作为低可信度参考。",
        search_url=search_url,
        items=items,
    )
