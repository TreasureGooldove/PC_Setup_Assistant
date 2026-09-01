"""通过可选 ModelScope/open-webSearch MCP 读取贴吧公开搜索摘要。

本模块是受控的只读连接器：只启动用户明确配置的 MCP 命令，只调用固定的
``search`` 工具，只保留贴吧链接、标题和短摘要。不会接收 Cookie、登录态、
验证码或任意 URL，也不会把原始 MCP 响应保存到数据库。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import Settings
from app.domain import CommunityEvidence

MAX_QUERY_LENGTH = 180
MAX_RESULTS = 8
MAX_TEXT_LENGTH = 400
TIEBA_HOSTS = {"tieba.baidu.com"}


class TiebaMcpError(RuntimeError):
    """贴吧 MCP 未能返回可用的公开搜索结果。"""


def _clip(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _text_blocks(result: Any) -> list[str]:
    blocks = getattr(result, "content", []) or []
    return [str(block.text) for block in blocks if getattr(block, "type", None) == "text"]


def _structured(result: Any) -> Mapping[str, Any]:
    payload = getattr(result, "structured_content", None)
    return payload if isinstance(payload, Mapping) else {}


def _payload(result: Any) -> Mapping[str, Any]:
    structured = _structured(result)
    if structured:
        return structured
    for block in _text_blocks(result):
        try:
            value = json.loads(block)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(value, Mapping):
            return value
    return {}


def _safe_tieba_url(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw or len(raw) > 1000:
        return None
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme != "https" or host not in TIEBA_HOSTS:
        return None
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        return None
    return raw


def _result_items(payload: Mapping[str, Any]) -> Sequence[Any]:
    for key in ("results", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, Mapping):
            nested = value.get("results") or value.get("items")
            if isinstance(nested, list):
                return nested
    return []


def parse_tieba_search_result(result: Any) -> list[CommunityEvidence]:
    """把 open-webSearch 的 JSON/文本结果收敛为低可信度社区摘要。"""

    if getattr(result, "is_error", False):
        raise TiebaMcpError("贴吧 MCP 返回错误")
    payload = _payload(result)
    evidence: list[CommunityEvidence] = []
    for item in _result_items(payload):
        if not isinstance(item, Mapping):
            continue
        url = _safe_tieba_url(item.get("url") or item.get("link"))
        if not url:
            continue
        title = _clip(item.get("title") or item.get("name"), 200) or "贴吧帖子"
        summary = _clip(
            item.get("description")
            or item.get("snippet")
            or item.get("summary")
            or "仅作为社区讨论入口，需自行核对原帖和发布时间。",
            MAX_TEXT_LENGTH,
        )
        item_id = hashlib.sha256(f"{title}\n{url}".encode()).hexdigest()[:24]
        evidence.append(
            CommunityEvidence(
                id=f"tieba:{item_id}",
                title=title,
                summary=summary,
                url=url,
                author=_clip(item.get("author") or item.get("user"), 100) or None,
                published_at=_clip(
                    item.get("published_at") or item.get("date") or item.get("time"),
                    60,
                )
                or None,
                source="百度贴吧（社区搜索）",
            )
        )
        if len(evidence) >= MAX_RESULTS:
            break
    return evidence


def _command_name(command: str) -> str:
    """Windows 下自动补全 npx.cmd，Linux/macOS 保留 npx。"""

    if os.name == "nt" and command.lower() == "npx":
        return "npx.cmd"
    return command


def _args(settings: Settings) -> list[str]:
    try:
        raw = json.loads(settings.modelscope_mcp_args_json)
    except json.JSONDecodeError as exc:
        raise TiebaMcpError("ModelScope MCP 参数不是有效 JSON") from exc
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise TiebaMcpError("ModelScope MCP 参数必须是字符串数组")
    if len(raw) > 16 or any(len(item) > 300 for item in raw):
        raise TiebaMcpError("ModelScope MCP 参数过长")
    return list(raw)


@dataclass
class _McpProcess:
    settings: Settings
    stack: AsyncExitStack | None = None
    session: ClientSession | None = None
    lock: asyncio.Lock | None = None

    def __post_init__(self) -> None:
        self.lock = asyncio.Lock()

    async def _ensure_session(self) -> ClientSession:
        if self.session is not None:
            return self.session
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        command = _command_name(self.settings.modelscope_mcp_command)
        params = StdioServerParameters(
            command=command,
            args=_args(self.settings),
            env=self.settings.modelscope_mcp_env,
            cwd=self.settings.modelscope_mcp_working_directory,
        )
        try:
            read_stream, write_stream = await self.stack.enter_async_context(
                # MCP SDK 要求 stderr 具备文件描述符；日志只进入服务进程 stderr，
                # 不会进入 API 响应、数据库或模型上下文。
                stdio_client(params, errlog=sys.stderr)
            )
            self.session = await self.stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await asyncio.wait_for(
                self.session.initialize(), timeout=self.settings.modelscope_mcp_timeout_seconds
            )
            tools = await asyncio.wait_for(
                self.session.list_tools(), timeout=self.settings.modelscope_mcp_timeout_seconds
            )
            if "search" not in {tool.name for tool in tools.tools}:
                raise TiebaMcpError("ModelScope MCP 未提供受支持的 search 工具")
            return self.session
        except Exception:
            await self.close()
            raise

    async def search(self, query: str) -> list[CommunityEvidence]:
        if self.lock is None:
            self.lock = asyncio.Lock()
        async with self.lock:
            session = await self._ensure_session()
            try:
                result = await asyncio.wait_for(
                    session.call_tool(
                        "search",
                        arguments={
                            "query": query,
                            "limit": min(self.settings.community_search_max_results, MAX_RESULTS),
                            "engines": ["baidu", "bing"],
                        },
                    ),
                    timeout=self.settings.modelscope_mcp_timeout_seconds,
                )
                return parse_tieba_search_result(result)
            except BaseException:
                # 超时、取消或传输异常后主动关闭 stdio，避免 npx/node 子进程残留。
                await self.close()
                raise

    async def close(self) -> None:
        if self.stack is not None:
            await self.stack.aclose()
        self.stack = None
        self.session = None


_processes: dict[tuple[str, str, str, str | None], _McpProcess] = {}


def _process_for(settings: Settings) -> _McpProcess:
    key = (
        settings.modelscope_mcp_command,
        settings.modelscope_mcp_args_json,
        settings.modelscope_mcp_env_json,
        settings.modelscope_mcp_working_directory,
    )
    process = _processes.get(key)
    if process is None:
        process = _McpProcess(settings)
        _processes[key] = process
    return process


async def search_tieba_mcp(query: str, settings: Settings) -> list[CommunityEvidence]:
    value = " ".join(query.split())
    if not value or len(value) > MAX_QUERY_LENGTH:
        raise ValueError("贴吧搜索词为空或超过 180 个字符")
    if not settings.modelscope_mcp_enabled:
        return []
    return await _process_for(settings).search(value)


async def close_modelscope_mcp_processes() -> None:
    processes = list(_processes.values())
    _processes.clear()
    for process in processes:
        await process.close()
