from __future__ import annotations

import html as html_module
import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin, urlparse

import httpx
from sqlalchemy import delete, select

from app.config import Settings, get_settings
from app.database import (
    CatalogPartRecord,
    CatalogSyncRecord,
    SessionLocal,
    json_dump,
    json_load,
)
from app.domain import Part, PartCategory
from app.features.builds.catalog import fixture_parts

PROVIDER_NAME = "ZOL 公开产品目录"
CATALOG_URLS: dict[PartCategory, str] = {
    PartCategory.CPU: "https://detail.zol.com.cn/cpu/",
    PartCategory.MOTHERBOARD: "https://detail.zol.com.cn/motherboard/",
    PartCategory.GPU: "https://detail.zol.com.cn/vga/",
    PartCategory.MEMORY: "https://detail.zol.com.cn/memory/",
    PartCategory.STORAGE: "https://detail.zol.com.cn/solid_state_drive/",
    PartCategory.PSU: "https://detail.zol.com.cn/power/",
    PartCategory.COOLING: "https://detail.zol.com.cn/cooling_product/",
    PartCategory.CASE: "https://detail.zol.com.cn/case/",
}

KNOWN_BRANDS = sorted(
    [
        "COLORFUL 七彩虹",
        "Fractal Design",
        "GIGABYTE 技嘉",
        "POWERCOLOR 撼讯",
        "SAPPHIRE 蓝宝石",
        "七彩虹",
        "九州风神",
        "乔思伯",
        "先马",
        "华硕",
        "微星",
        "技嘉",
        "铭瑄",
        "盈通",
        "讯景",
        "影驰",
        "耕升",
        "映众",
        "瀚铠",
        "蓝戟",
        "万丽",
        "索泰",
        "蓝宝石",
        "撼讯",
        "迪兰",
        "华擎",
        "丽台",
        "PNY",
        "利民",
        "瓦尔基里",
        "酷冷至尊",
        "海盗船",
        "海韵",
        "安钛克",
        "振华",
        "长城",
        "联力",
        "猫头鹰",
        "三星",
        "金士顿",
        "雷克沙",
        "西部数据",
        "英睿达",
        "芝奇",
        "光威",
        "阿斯加特",
        "十铨",
        "Solidigm",
        "NZXT",
        "Intel",
        "AMD",
    ],
    key=len,
    reverse=True,
)


def validate_catalog_url(category: PartCategory, url: str) -> str:
    expected = CATALOG_URLS[category]
    parsed = urlparse(url)
    if (
        url != expected
        or parsed.scheme != "https"
        or parsed.hostname != "detail.zol.com.cn"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("目录同步地址不在固定白名单中")
    return url


def _plain_text(fragment: str) -> str:
    value = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_module.unescape(value)).strip()


def _brand_from_name(name: str) -> str:
    normalized = name.strip()
    for brand in KNOWN_BRANDS:
        if normalized.casefold().startswith(brand.casefold()):
            return brand
    if "/" in normalized:
        return normalized.split("/", 1)[0].strip()[:40]
    token = re.split(r"[\s·]", normalized, maxsplit=1)[0]
    return token[:40] or "待确认"


def _catalog_kind(category: PartCategory, text: str) -> str:
    upper = text.upper()
    if category == PartCategory.GPU:
        match = re.search(
            r"\b(RTX\s*\d{4}(?:\s*TI|\s*SUPER)?|RX\s*\d{4}(?:\s*XTX|\s*XT|\s*GRE)?)\b",
            upper,
        )
        if not match:
            return "其他型号"
        return re.sub(r"\s+", " ", match.group(1)).title().replace("Rtx", "RTX").replace("Rx", "RX")
    if category == PartCategory.CPU:
        for pattern, label in (
            (r"RYZEN\s*9", "Ryzen 9"),
            (r"RYZEN\s*7", "Ryzen 7"),
            (r"RYZEN\s*5", "Ryzen 5"),
            (r"CORE\s*ULTRA", "Core Ultra"),
            (r"\bI9[- ]", "Core i9"),
            (r"\bI7[- ]", "Core i7"),
            (r"\bI5[- ]", "Core i5"),
            (r"\bI3[- ]", "Core i3"),
        ):
            if re.search(pattern, upper):
                return label
        return "其他系列"
    if category == PartCategory.COOLING:
        return "水冷散热器" if re.search(r"水冷|冷排|一体式|橡胶管", text) else "风冷散热器"
    if category == PartCategory.MEMORY:
        match = re.search(r"DDR[345]", upper)
        return match.group(0) if match else "其他内存"
    if category == PartCategory.STORAGE:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)", upper)
        return f"{match.group(1)}{match.group(2)}" if match else "其他容量"
    if category == PartCategory.PSU:
        match = re.search(r"(\d{3,4})\s*W", upper)
        return f"{match.group(1)}W" if match else "其他功率"
    if category in {PartCategory.MOTHERBOARD, PartCategory.CASE}:
        if "MINI-ITX" in upper or "ITX" in upper:
            return "Mini-ITX"
        if "MATX" in upper or "M-ATX" in upper:
            return "mATX"
        if "ATX" in upper:
            return "ATX"
    return "其他"


def _infer_specs(category: PartCategory, name: str, summary: str) -> tuple[dict[str, object], int]:
    text = f"{name} {summary}"
    upper = text.upper()
    kind = _catalog_kind(category, text)
    specs: dict[str, object] = {"catalog_kind": kind}
    power_w = 0
    if category == PartCategory.GPU:
        vram = re.search(r"(\d+)\s*GB", upper)
        bus = re.search(r"(\d{2,3})\s*BIT", upper)
        memory_type = re.search(r"GDDR[5-7](?:X)?", upper)
        if vram:
            specs["vram_gb"] = int(vram.group(1))
        if bus:
            specs["memory_bus_bit"] = int(bus.group(1))
        if memory_type:
            specs["memory_type"] = memory_type.group(0)
        power_map = {
            "RTX 5090": 575,
            "RTX 5080": 360,
            "RTX 5070 Ti": 300,
            "RTX 5070": 250,
            "RTX 5060 Ti": 180,
            "RTX 5060": 145,
            "RX 9070 Xtx": 355,
            "RX 9070 Xt": 304,
            "RX 9070": 220,
        }
        power_w = power_map.get(kind, 0)
        specs["chipset"] = kind
    elif category == PartCategory.MEMORY:
        memory_type = re.search(r"DDR[345]", upper)
        capacity = re.search(r"(\d+)\s*GB", upper)
        if memory_type:
            specs["memory_type"] = memory_type.group(0)
        if capacity:
            specs["capacity_gb"] = int(capacity.group(1))
    elif category == PartCategory.STORAGE:
        capacity = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)", upper)
        if capacity:
            value = float(capacity.group(1))
            specs["capacity_gb"] = int(value * 1024 if capacity.group(2) == "TB" else value)
        specs["connector"] = "SATA" if "SATA" in upper else "M.2"
    elif category == PartCategory.PSU:
        wattage = re.search(r"(\d{3,4})\s*W", upper)
        if wattage:
            specs["wattage"] = int(wattage.group(1))
    elif category == PartCategory.COOLING:
        cooling_type = "water" if kind == "水冷散热器" else "air"
        specs["type"] = cooling_type
        radiator = re.search(r"\b(120|240|280|360|420)\b", upper)
        if cooling_type == "water" and radiator:
            specs["radiator_mm"] = int(radiator.group(1))
    elif category in {PartCategory.MOTHERBOARD, PartCategory.CASE}:
        specs["form_factor"] = kind if kind in {"ATX", "mATX", "Mini-ITX"} else None
    return specs, power_w


def parse_zol_catalog_html(
    page: str,
    category: PartCategory,
    *,
    source_url: str | None = None,
    max_items: int = 40,
    captured_at: datetime | None = None,
) -> list[Part]:
    source_url = source_url or CATALOG_URLS[category]
    validate_catalog_url(category, source_url)
    captured = captured_at or datetime.now(UTC)
    items: list[Part] = []
    pattern = re.compile(r'<li\b[^>]*data-follow-id=["\']p(\d+)["\'][^>]*>(.*?)</li>', re.I | re.S)
    for product_id, body in pattern.findall(page):
        link_match = re.search(r'href=["\']([^"\']*index\d+\.shtml)["\']', body, re.I)
        title_match = re.search(r"<h3[^>]*>\s*<a[^>]*>(.*?)</a>\s*</h3>", body, re.I | re.S)
        price_match = re.search(r'class=["\']price-type["\'][^>]*>\s*([\d,.]+)\s*<', body, re.I)
        if not link_match or not title_match or not price_match:
            continue
        title_html = title_match.group(1)
        summary_match = re.search(r"<span[^>]*>(.*?)</span>", title_html, re.I | re.S)
        summary = _plain_text(summary_match.group(1)) if summary_match else ""
        name = _plain_text(re.sub(r"<span[^>]*>.*?</span>", "", title_html, flags=re.I | re.S))
        if not name:
            continue
        price = float(price_match.group(1).replace(",", ""))
        image_match = re.search(r'(?:\.src|src)=["\'](https?://[^"\']+)["\']', body, re.I)
        specs, power_w = _infer_specs(category, name, summary)
        items.append(
            Part(
                id=f"zol-{category.value}-{product_id}",
                category=category,
                name=name,
                brand=_brand_from_name(name),
                price=price,
                source=PROVIDER_NAME,
                url=urljoin(source_url, link_match.group(1)),
                image_url=image_match.group(1) if image_match else None,
                specs=specs,
                power_w=power_w,
                summary=summary or "来自公开产品列表的候选，关键兼容参数缺失时会标记待确认。",
                advantages=["公开产品目录中的具体厂商型号，可与同芯片不同品牌进行比价。"],
                cautions=["页面价格是公开参考价，不代表实时最低价或最终到手价。"],
                data_updated_at=captured.date().isoformat(),
            )
        )
        if len(items) >= max_items:
            break
    return items


async def fetch_zol_catalog(category: PartCategory, settings: Settings | None = None) -> list[Part]:
    configured = settings or get_settings()
    url = validate_catalog_url(category, CATALOG_URLS[category])
    timeout = httpx.Timeout(configured.catalog_sync_timeout_seconds)
    headers = {
        "User-Agent": "PCSetupAssistant/0.1 public-catalog-sync",
        "Accept": "text/html",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        headers=headers,
    ) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            if response.is_redirect:
                raise ValueError("目录页面发生重定向，已停止同步")
            if "text/html" not in response.headers.get("content-type", "").lower():
                raise ValueError("目录页面未返回 HTML")
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > configured.catalog_sync_max_response_bytes:
                    raise ValueError("目录页面超过响应大小限制")
                chunks.append(chunk)
            encoding = response.encoding or "gb18030"
    page = b"".join(chunks).decode(encoding, errors="replace")
    return parse_zol_catalog_html(
        page,
        category,
        source_url=url,
        max_items=configured.catalog_sync_max_items,
    )


def _normalized_key(part: Part) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", f"{part.brand}{part.name}".casefold())


def cached_parts(category: PartCategory | None = None) -> list[Part]:
    with SessionLocal() as session:
        query = select(CatalogPartRecord)
        if category is not None:
            query = query.where(CatalogPartRecord.category == category.value)
        records = session.scalars(query.order_by(CatalogPartRecord.captured_at.desc())).all()
        return [Part.model_validate(json_load(record.part_json, {})) for record in records]


def merged_catalog(category: PartCategory) -> list[Part]:
    cached = cached_parts(category)
    fixtures = [part for part in fixture_parts() if part.category == category]
    seen: set[str] = set()
    merged: list[Part] = []
    for part in [*cached, *fixtures]:
        key = _normalized_key(part)
        if key in seen:
            continue
        seen.add(key)
        merged.append(part)
    return merged


def find_catalog_part(part_id: str) -> Part | None:
    fixture = next((part for part in fixture_parts() if part.id == part_id), None)
    if fixture:
        return fixture
    with SessionLocal() as session:
        record = session.get(CatalogPartRecord, part_id)
        return Part.model_validate(json_load(record.part_json, {})) if record else None


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def catalog_sync_status(
    category: PartCategory, settings: Settings | None = None
) -> dict[str, object]:
    configured = settings or get_settings()
    with SessionLocal() as session:
        record = session.get(CatalogSyncRecord, category.value)
        captured_at = _as_utc(record.captured_at) if record else None
        updated_at = _as_utc(record.updated_at) if record else None
        stale = captured_at is None or captured_at < datetime.now(UTC) - timedelta(
            hours=configured.catalog_sync_ttl_hours
        )
        return {
            "enabled": configured.catalog_public_sync_enabled,
            "status": record.status if record else "never",
            "provider": record.provider if record else PROVIDER_NAME,
            "item_count": record.item_count if record else 0,
            "message": record.message if record else "尚未同步，当前展示本地参考候选",
            "updated_at": updated_at.isoformat() if updated_at else None,
            "stale": stale,
            "source_url": CATALOG_URLS[category],
        }


def _write_sync_state(
    category: PartCategory,
    status: str,
    message: str,
    *,
    item_count: int | None = None,
    captured_at: datetime | None = None,
) -> None:
    now = datetime.now(UTC)
    with SessionLocal() as session:
        record = session.get(CatalogSyncRecord, category.value)
        if record is None:
            record = CatalogSyncRecord(category=category.value, status=status)
            session.add(record)
        record.status = status
        record.provider = PROVIDER_NAME
        record.message = message[:300]
        if item_count is not None:
            record.item_count = item_count
        if captured_at is not None:
            record.captured_at = captured_at
        record.updated_at = now
        session.commit()


def mark_sync_queued(category: PartCategory) -> None:
    _write_sync_state(category, "queued", "目录更新已进入后台队列")


def save_catalog_parts(category: PartCategory, parts: list[Part], settings: Settings) -> None:
    captured = datetime.now(UTC)
    expires = captured + timedelta(hours=settings.catalog_sync_ttl_hours)
    with SessionLocal() as session:
        session.execute(
            delete(CatalogPartRecord).where(CatalogPartRecord.category == category.value)
        )
        session.add_all(
            [
                CatalogPartRecord(
                    id=part.id,
                    category=category.value,
                    source=PROVIDER_NAME,
                    part_json=json_dump(part.model_dump(mode="json")),
                    captured_at=captured,
                    expires_at=expires,
                )
                for part in parts
            ]
        )
        state = session.get(CatalogSyncRecord, category.value)
        if state is None:
            state = CatalogSyncRecord(category=category.value, status="completed")
            session.add(state)
        state.status = "completed"
        state.provider = PROVIDER_NAME
        state.item_count = len(parts)
        state.message = f"已更新 {len(parts)} 个公开厂商型号"
        state.captured_at = captured
        state.updated_at = captured
        session.commit()


async def sync_catalog(
    category: PartCategory, settings: Settings | None = None
) -> dict[str, object]:
    configured = settings or get_settings()
    if not configured.catalog_public_sync_enabled:
        raise ValueError("公开目录同步未启用")
    _write_sync_state(category, "running", "正在读取固定白名单公开产品目录")
    try:
        parts = await fetch_zol_catalog(category, configured)
        if not parts:
            raise ValueError("公开目录未解析到可用候选")
        save_catalog_parts(category, parts, configured)
        return {"category": category.value, "item_count": len(parts)}
    except Exception as exc:
        _write_sync_state(category, "unavailable", f"更新失败，保留已有候选：{str(exc)[:220]}")
        raise


def query_catalog(
    category: PartCategory,
    *,
    query: str = "",
    brand: str | None = None,
    kind: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "default",
) -> dict[str, object]:
    all_items = merged_catalog(category)
    brand_counts = Counter(part.brand for part in all_items)
    kind_counts = Counter(str(part.specs.get("catalog_kind", "其他")) for part in all_items)
    needle = query.strip().casefold()
    items = [
        part
        for part in all_items
        if (not needle or needle in f"{part.name} {part.brand} {part.summary}".casefold())
        and (not brand or brand == "all" or part.brand == brand)
        and (not kind or kind == "all" or str(part.specs.get("catalog_kind", "其他")) == kind)
        and (min_price is None or part.price >= min_price)
        and (max_price is None or part.price <= max_price)
    ]
    if sort == "price_asc":
        items.sort(key=lambda part: (part.price, part.name))
    elif sort == "price_desc":
        items.sort(key=lambda part: (-part.price, part.name))
    elif sort == "brand":
        items.sort(key=lambda part: (part.brand, part.price))
    prices = [part.price for part in all_items]
    return {
        "items": [part.model_dump(mode="json") for part in items],
        "total": len(items),
        "facets": {
            "brands": [
                {"value": value, "label": value, "count": count}
                for value, count in sorted(
                    brand_counts.items(), key=lambda item: (-item[1], item[0])
                )
            ],
            "kinds": [
                {"value": value, "label": value, "count": count}
                for value, count in sorted(
                    kind_counts.items(), key=lambda item: (-item[1], item[0])
                )
            ],
            "price_min": min(prices) if prices else 0,
            "price_max": max(prices) if prices else 0,
        },
        "sync": catalog_sync_status(category),
    }
