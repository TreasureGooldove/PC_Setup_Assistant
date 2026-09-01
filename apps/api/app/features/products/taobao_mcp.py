"""淘宝 MCP 的可选连接器。

第三方 MCP 服务作为独立进程运行。本模块只负责标准 MCP 会话、结果提取和
报价字段归一化，不复制第三方抓取代码，也不处理验证码、登录态或访问控制。
"""

from __future__ import annotations

import asyncio
import io
import re
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import Settings
from app.domain import Offer, Part
from app.features.builds.price_sources import normalize_offer

MAX_REFERENCE_LENGTH = 500
ALLOWED_HOSTS = {"taobao.com", "tmall.com", "e.tb.cn"}


class TaobaoMcpError(RuntimeError):
    """淘宝 MCP 未能返回可核验数据。"""


@dataclass
class TaobaoMcpResult:
    offer: Offer | None = None
    title: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    note: str = ""
    status: str = "unavailable"


def validate_product_reference(reference: str) -> str:
    value = reference.strip()
    if not value or len(value) > MAX_REFERENCE_LENGTH:
        raise ValueError("淘宝商品链接或 ID 为空，或超过 500 个字符")
    if re.fullmatch(r"\d{6,20}", value):
        return value

    urls = re.findall(r"https?://[^\s】)]+", value)
    if not urls:
        raise ValueError("淘宝商品引用需要数字商品 ID、淘宝/天猫链接或分享文本")
    for raw_url in urls:
        parsed = urlparse(raw_url)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise ValueError("淘宝商品引用只允许 HTTPS 链接，不接受带账号信息的地址")
        if not any(host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_HOSTS):
            raise ValueError("淘宝商品引用的域名不在允许范围内")
    return value


def _text_blocks(result: Any) -> list[str]:
    blocks = getattr(result, "content", []) or []
    return [str(block.text) for block in blocks if getattr(block, "type", None) == "text"]


def _structured(result: Any) -> Mapping[str, Any]:
    payload = getattr(result, "structured_content", None)
    return payload if isinstance(payload, Mapping) else {}


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _find_value(text: str, labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:{label_pattern})\s*[：:]?\s*[`* ]*([^\n|｜]+)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = re.sub(r"[*`#]+", "", match.group(1)).strip(" ：:")
    return value or None


def _money_text(value: Any) -> float | None:
    if value in (None, ""):
        return None
    match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", str(value))
    return float(match.group(0).replace(",", "")) if match else None


_PARAMETER_ALIASES = {
    "品牌": "brand_name",
    "型号": "model",
    "商品名称": "product_name",
    "系列": "series",
    "芯片厂商": "chipset_vendor",
    "显卡芯片": "gpu_chip",
    "核心数量": "physical_cores",
    "核心数": "physical_cores",
    "线程数量": "logical_threads",
    "线程数": "logical_threads",
    "核心线程": "cores_threads",
    "主频": "base_clock",
    "基础频率": "base_clock",
    "加速频率": "boost_clock",
    "二级缓存": "l2_cache",
    "三级缓存": "l3_cache",
    "核显": "integrated_graphics",
    "功率": "tdp",
    "设计功耗": "tdp",
    "制程工艺": "process",
    "架构": "architecture",
    "上市年份": "launch_year",
    "上市日期": "launch_date",
    "内存支持": "memory_types",
    "内存类型": "memory_type",
    "CPU插槽": "socket",
    "适用CPU接口": "socket",
    "板型": "form_factor",
    "芯片组": "chipset",
    "最大内存容量": "max_memory",
    "内存插槽数量": "memory_slots",
    "最高内存频率": "max_memory_speed",
    "PCIe版本": "pcie_version",
    "M.2接口数量": "m2_slots",
    "SATA接口数量": "sata_ports",
    "无线标准": "wifi",
    "蓝牙": "bluetooth",
    "有线网卡": "lan",
    "显存容量": "vram_gb",
    "显存类型": "memory_type",
    "显存位宽": "memory_bus_bit",
    "显存频率": "memory_clock",
    "CUDA核心": "cuda_cores",
    "流处理器": "stream_processors",
    "最大分辨率": "max_resolution",
    "I/O接口": "outputs",
    "视频输出": "outputs",
    "供电接口": "power_connectors",
    "建议电源": "recommended_psu_w",
    "整卡功耗": "tgp",
    "显卡长度": "length_mm",
    "产品尺寸": "dimensions",
    "插槽": "slot_count",
    "内存频率": "speed_mts",
    "时序": "timings",
    "工作电压": "voltage",
    "传输协议": "protocol",
    "主控": "controller",
    "闪存类型": "nand",
    "额定功率": "wattage",
    "80PLUS认证": "rating",
    "模组类型": "modular",
    "ATX版本": "atx_version",
    "PCIe接口数量": "pcie_8pin_count",
    "12VHPWR接口": "twelve_vhpwr",
    "散热方式": "cooling",
    "散热器高度": "height_mm",
    "冷排尺寸": "radiator_mm",
    "风扇转速": "fan_speed_rpm",
    "噪音": "noise_db",
    "支持平台": "supported_sockets",
    "支持板型": "supported_form_factors",
    "显卡限长": "gpu_length_mm",
    "风冷限高": "cooler_height_mm",
    "前置接口": "front_io",
}


def _canonical_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    result = {str(key): value for key, value in parameters.items() if value not in (None, "")}
    for key, value in list(result.items()):
        normalized_key = re.sub(r"\s+", "", key)
        canonical_key = _PARAMETER_ALIASES.get(key) or _PARAMETER_ALIASES.get(normalized_key)
        if canonical_key and canonical_key not in result:
            result[canonical_key] = value
    return result


def _parameter_map(payload: Mapping[str, Any], text: str) -> dict[str, Any]:
    raw = _first(payload, "parameters", "specifications", "props", "商品参数", "参数")
    if isinstance(raw, Mapping):
        return _canonical_parameters(raw)
    parameters: dict[str, Any] = {}
    for line in text.splitlines():
        match = re.match(r"\s*(?:[-*]|\|)?\s*([^:：|｜]{1,30})\s*[：:]\s*([^|｜]+)", line)
        if match:
            key, value = match.group(1).strip(), match.group(2).strip()
            if key and value and key not in {"价格", "店铺", "商品标题"}:
                parameters[key] = value
    return _canonical_parameters(parameters)


def parse_product_result(
    part: Part,
    result: Any,
    reference: str,
    captured_at: datetime | None = None,
) -> TaobaoMcpResult:
    """从 MCP 的结构化或 Markdown 返回中提取可核验价格和店铺。"""

    payload = _structured(result)
    text = "\n".join(_text_blocks(result))
    if getattr(result, "is_error", False):
        return TaobaoMcpResult(
            note=text[:300] or "淘宝 MCP 返回错误",
            status="unavailable",
        )
    title = _first(payload, "title", "product_title", "name", "商品标题", "商品名称")
    title = (
        str(title)
        if title is not None
        else _find_value(text, ("商品标题", "商品名称", "标题", "Product Title", "Title"))
    )
    seller = _first(payload, "store_name", "shop_name", "shop_title", "mall_name", "seller_nick")
    seller = (
        str(seller)
        if seller is not None
        else _find_value(text, ("店铺名称", "店铺", "商店", "Store", "Shop"))
    )
    product_id = _first(payload, "product_id", "item_id", "商品 ID", "商品ID")
    product_id = (
        str(product_id)
        if product_id is not None
        else _find_value(text, ("商品 ID", "商品ID", "Product ID"))
    )
    url = _first(payload, "url", "product_url", "商品链接") or reference

    list_raw = _first(payload, "reserve_price", "original_price", "list_price", "原价")
    price_raw = _first(
        payload,
        "zk_final_price",
        "discount_price",
        "final_price",
        "price",
        "current_price",
        "售价",
        "价格",
    )
    coupon_raw = _first(payload, "coupon_amount", "coupon_discount", "优惠券")
    list_price = _money_text(list_raw)
    price = _money_text(price_raw)
    coupon = _money_text(coupon_raw)
    if price is None:
        price = _money_text(
            _find_value(text, ("券后价", "到手价", "当前价", "售价", "价格", "Price"))
        )
    if list_price is None:
        list_price = _money_text(_find_value(text, ("原价", "划线价")))
    if coupon is None:
        coupon = _money_text(_find_value(text, ("优惠券", "优惠")))
    if price is None:
        return TaobaoMcpResult(
            title=title,
            parameters=_parameter_map(payload, text),
            note="淘宝 MCP 已返回内容，但未解析到明确价格，未将其标记为实时报价。",
            status="unavailable",
        )

    normalized_payload: dict[str, Any] = {
        "item_id": product_id,
        "reserve_price": list_price or price,
        "zk_final_price": price,
        # 商品页通常已经把券后/活动价展示为当前价；避免把优惠券重复扣除。
        "coupon_amount": None,
        "store_name": seller,
        "url": str(url) if url else reference,
    }
    offer = normalize_offer(
        part.id,
        "taobao",
        normalized_payload,
        captured_at=captured_at or datetime.now(UTC),
        price_unit="yuan",
    )
    if offer is None:
        return TaobaoMcpResult(
            title=title,
            parameters=_parameter_map(payload, text),
            note="淘宝 MCP 返回的价格字段未通过金额校验，未将其标记为实时报价。",
            status="unavailable",
        )
    offer = offer.model_copy(
        update={
            "source": "淘宝 MCP",
            "seller": seller or offer.seller,
            "status": "实时读取（淘宝 MCP）",
            "is_live": True,
            "sku": product_id or offer.sku,
            "url": str(url) if url else reference,
            "coupon_note": f"优惠信息约 ¥{coupon:.2f}" if coupon else offer.coupon_note,
        }
    )
    return TaobaoMcpResult(
        offer=offer,
        title=title,
        parameters=_parameter_map(payload, text),
        note=(
            "已通过淘宝 MCP 读取店铺与价格，采集时间为 "
            f"{offer.captured_at.isoformat() if offer.captured_at else '待确认'}。"
        ),
        status="live",
    )


def _pagination(result: Any) -> tuple[bool, int | None]:
    payload = _structured(result)
    has_more = _first(payload, "has_more", "hasMore", "还有更多")
    next_offset = _first(payload, "next_offset", "nextOffset", "下一页偏移")
    text = "\n".join(_text_blocks(result))
    if has_more is None:
        match = re.search(r"has_more\s*[=:：]\s*(true|false)", text, re.IGNORECASE)
        has_more = match.group(1).lower() == "true" if match else False
    if next_offset is None:
        match = re.search(r"next_offset\s*[=:：]\s*(\d+)", text, re.IGNORECASE)
        next_offset = int(match.group(1)) if match else None
    return bool(has_more), int(next_offset) if next_offset is not None else None


class _McpProcess:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None
        self.ready = False
        self.lock = asyncio.Lock()
        self.fetch_tool = settings.taobao_mcp_fetch_tool

    async def _ensure_session(self) -> ClientSession:
        if self.session is not None:
            return self.session
        server_path = Path(self.settings.taobao_mcp_server_path).expanduser()
        if not server_path.is_file():
            raise TaobaoMcpError(f"淘宝 MCP server.py 不存在：{server_path}")
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        params = StdioServerParameters(
            command=self.settings.taobao_mcp_command,
            args=[str(Path(__file__).with_name("taobao_mcp_launcher.py")), str(server_path)],
            cwd=self.settings.taobao_mcp_working_directory,
        )
        try:
            read_stream, write_stream = await self.stack.enter_async_context(
                stdio_client(params, errlog=io.StringIO())
            )
            self.session = await self.stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            available = await self.session.list_tools()
            names = {tool.name for tool in available.tools}
            if self.fetch_tool not in names:
                legacy_name = "taobao_fetch_product_info"
                if self.fetch_tool == "taobao_fetch_product" and legacy_name in names:
                    self.fetch_tool = legacy_name
            return self.session
        except Exception:
            await self.close()
            raise

    async def _initialize_login(self, session: ClientSession) -> None:
        if self.ready:
            return
        result = await session.call_tool("taobao_initialize_login", arguments={})
        text = "\n".join(_text_blocks(result))
        normalized = text.casefold()
        if "login_required" in normalized or "扫码" in text:
            raise TaobaoMcpError("淘宝 MCP 需要先在其浏览器窗口完成扫码登录")
        if "error" in normalized and "ready" not in normalized:
            raise TaobaoMcpError(text[:300] or "淘宝 MCP 初始化失败")
        self.ready = True

    async def fetch(self, reference: str) -> list[Any]:
        async with self.lock:
            session = await self._ensure_session()
            await self._initialize_login(session)
            results: list[Any] = []
            offset = 0
            for _ in range(20):
                result = await session.call_tool(
                    self.fetch_tool,
                    arguments={"product_url_or_id": reference, "offset": offset, "limit": 20},
                )
                results.append(result)
                has_more, next_offset = _pagination(result)
                if not has_more or next_offset is None or next_offset <= offset:
                    break
                offset = next_offset
            return results

    async def close(self) -> None:
        if self.stack is not None:
            await self.stack.aclose()
        self.stack = None
        self.session = None
        self.ready = False


_processes: dict[tuple[str, str, str | None], _McpProcess] = {}


def _process_for(settings: Settings) -> _McpProcess:
    key = (
        settings.taobao_mcp_command,
        str(Path(settings.taobao_mcp_server_path).expanduser()),
        settings.taobao_mcp_working_directory,
    )
    process = _processes.get(key)
    if process is None:
        process = _McpProcess(settings)
        _processes[key] = process
    return process


async def fetch_taobao_offer(part: Part, settings: Settings) -> TaobaoMcpResult:
    if not settings.taobao_mcp_enabled:
        return TaobaoMcpResult(status="disabled", note="淘宝 MCP 未启用。")
    reference = settings.taobao_product_urls.get(part.id)
    if not reference:
        return TaobaoMcpResult(status="unconfigured", note="当前型号未配置淘宝商品链接或商品 ID。")
    try:
        validated = validate_product_reference(reference)
        results = await _process_for(settings).fetch(validated)
        if not results:
            raise TaobaoMcpError("淘宝 MCP 未返回商品内容")
        parsed_results = [parse_product_result(part, item, validated) for item in results]
        parsed = next(
            (item for item in parsed_results if item.offer is not None), parsed_results[0]
        )
        for item in parsed_results:
            parsed.parameters.update(item.parameters)
            parsed.title = parsed.title or item.title
        return parsed
    except (TaobaoMcpError, ValueError, OSError) as exc:
        return TaobaoMcpResult(status="unavailable", note=str(exc)[:300])
    except Exception as exc:
        return TaobaoMcpResult(status="unavailable", note=f"淘宝 MCP 调用失败：{str(exc)[:240]}")


async def close_taobao_mcp_processes() -> None:
    processes = list(_processes.values())
    _processes.clear()
    for process in processes:
        await process.close()
