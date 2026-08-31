from __future__ import annotations

import html as html_module
import json
import re
from datetime import UTC, datetime
from urllib.parse import quote, urlparse

import httpx

from app.config import Settings, get_settings
from app.domain import DataSourceStatus, Evidence, Offer, Part, PartCategory, ProductDetail
from app.errors import NotFoundError
from app.features.builds.catalog import fixture_parts
from app.features.builds.catalog_expansion import CPU_LADDER_URL, DIY_SOURCE_URL, GPU_LADDER_URL

MAX_JD_HTML_BYTES = 2_000_000


def validate_jd_product_url(url: str) -> str:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "item.jd.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or not re.fullmatch(r"/\d+\.html", parsed.path)
    ):
        raise ValueError("京东商品地址必须是 https://item.jd.com/<数字>.html")
    return url


def _plain_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_module.unescape(text)).strip()


def parse_jd_product_html(page: str) -> tuple[str | None, dict[str, str]]:
    """解析公开 HTML 中的标题、JSON-LD 与 dt/dd 参数，不执行 JavaScript。"""

    title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    title = _plain_text(title_match.group(1)) if title_match else None
    parameters: dict[str, str] = {}
    label_map = {
        "品牌": "brand_name",
        "型号": "model",
        "商品名称": "product_name",
        "适用CPU接口": "socket",
        "CPU插槽": "socket",
        "板型": "form_factor",
        "内存类型": "memory_type",
        "最大内存容量": "max_memory",
        "芯片组": "chipset",
        "M.2接口数量": "m2_slots",
        "SATA接口数量": "sata_ports",
        "无线标准": "wifi",
    }
    for raw_label, raw_value in re.findall(
        r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", page, re.I | re.S
    ):
        label, value = _plain_text(raw_label), _plain_text(raw_value)
        if label and value:
            parameters[label_map.get(label, f"jd_{label}")] = value

    for raw_json in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page,
        re.I | re.S,
    ):
        try:
            payload = json.loads(html_module.unescape(raw_json).strip())
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict):
            if payload.get("name") and not title:
                title = str(payload["name"])
            properties = payload.get("additionalProperty", [])
            if isinstance(properties, list):
                for item in properties:
                    if not isinstance(item, dict) or not item.get("name") or not item.get("value"):
                        continue
                    label = str(item["name"])
                    parameters[label_map.get(label, f"jd_{label}")] = str(item["value"])
    return title, parameters


async def fetch_jd_public_parameters(url: str) -> tuple[str | None, dict[str, str]]:
    safe_url = validate_jd_product_url(url)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(8.0),
        follow_redirects=False,
        trust_env=False,
        headers={"User-Agent": "PC-Setup-Assistant/0.1 public-product-metadata"},
    ) as client:
        response = await client.get(safe_url)
    response.raise_for_status()
    if response.is_redirect:
        raise ValueError("京东商品页发生重定向，已停止解析")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ValueError("京东商品页未返回 HTML")
    if len(response.content) > MAX_JD_HTML_BYTES:
        raise ValueError("京东商品页超过解析大小限制")
    return parse_jd_product_html(response.text)


def fixture_offers(part: Part, captured_at: datetime | None = None) -> list[Offer]:
    captured = captured_at or datetime.now(UTC)
    keyword = quote(part.name)
    rows = (
        (
            "jd",
            "京东示例报价",
            1.0,
            "京东搜索入口",
            f"https://search.jd.com/Search?keyword={keyword}",
        ),
        (
            "pdd",
            "拼多多示例报价",
            0.96,
            "拼多多搜索入口",
            f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}",
        ),
    )
    offers: list[Offer] = []
    for platform, source, ratio, seller, url in rows:
        landed = round(part.price * ratio, 2)
        offers.append(
            Offer(
                part_id=part.id,
                price=landed,
                source=source,
                platform=platform,
                list_price=round(part.price * 1.05, 2),
                discount_price=landed,
                landed_price=landed,
                seller=seller,
                status="示例报价（未联网）",
                url=url,
                captured_at=captured,
                is_live=False,
            )
        )
    return offers


def _reference_evidence(part: Part) -> list[Evidence]:
    if part.category == PartCategory.CPU:
        title, url = "ZOL CPU 天梯", CPU_LADDER_URL
    elif part.category == PartCategory.GPU:
        title, url = "ZOL 显卡天梯", GPU_LADDER_URL
    else:
        title, url = "ZOL DIY 硬件频道", DIY_SOURCE_URL
    return [
        Evidence(
            source="中关村在线",
            title=title,
            url=url,
            summary="用于型号层级、参数字段和资料入口参考；价格不作为实时成交价。",
            confidence="medium",
        ),
        Evidence(
            source="本地结构化目录",
            title=f"{part.name} 兼容性参数",
            url=part.url,
            summary="插槽、内存代际、板型、尺寸和供电字段会交给确定性规则复核。",
            confidence="medium",
        ),
    ]


async def get_product_detail(part_id: str, settings: Settings | None = None) -> ProductDetail:
    configured = settings or get_settings()
    part = next((item for item in fixture_parts() if item.id == part_id), None)
    if part is None:
        raise NotFoundError("商品", part_id)
    result_part = part.model_copy(deep=True)
    captured = datetime.now(UTC)
    sources = [
        DataSourceStatus(
            provider="本地结构化目录",
            kind="parameters",
            status="reference",
            note="默认参数，可复现并参与兼容性校验。",
            url=part.url,
            captured_at=captured,
        )
    ]
    evidence = _reference_evidence(part)
    jd_url = configured.jd_product_urls.get(part_id)
    if not configured.jd_public_fetch_enabled:
        sources.append(
            DataSourceStatus(
                provider="京东公开商品页",
                kind="parameters",
                status="disabled",
                note="公开页参数解析默认关闭；启用后仍不会使用登录态或反爬绕过。",
                url=jd_url,
            )
        )
    elif not jd_url:
        sources.append(
            DataSourceStatus(
                provider="京东公开商品页",
                kind="parameters",
                status="unconfigured",
                note="当前型号未配置京东商品页地址，继续使用结构化目录。",
            )
        )
    else:
        try:
            title, parameters = await fetch_jd_public_parameters(jd_url)
            result_part.specs.update(parameters)
            sources.append(
                DataSourceStatus(
                    provider="京东公开商品页",
                    kind="parameters",
                    status="live",
                    note=f"已读取公开 HTML 参数{f'：{title}' if title else ''}。",
                    url=jd_url,
                    captured_at=captured,
                )
            )
            evidence.append(
                Evidence(
                    source="京东公开商品页",
                    title=title or part.name,
                    url=jd_url,
                    summary=f"解析到 {len(parameters)} 个公开参数字段。",
                    confidence="medium",
                )
            )
        except (httpx.HTTPError, ValueError) as exc:
            sources.append(
                DataSourceStatus(
                    provider="京东公开商品页",
                    kind="parameters",
                    status="unavailable",
                    note=f"公开页读取失败，已回退结构化目录：{str(exc)[:100]}",
                    url=jd_url,
                    captured_at=captured,
                )
            )
    sources.extend(
        [
            DataSourceStatus(
                provider="京东",
                kind="price",
                status="fixture",
                note="示例报价，点击后请在平台核对实时价。",
                captured_at=captured,
            ),
            DataSourceStatus(
                provider="拼多多",
                kind="price",
                status="fixture",
                note="示例报价，点击后请在平台核对实时价。",
                captured_at=captured,
            ),
        ]
    )
    return ProductDetail(
        part=result_part,
        offers=fixture_offers(result_part, captured),
        evidence=evidence,
        sources=sources,
    )
