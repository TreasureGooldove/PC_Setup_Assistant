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
from app.features.builds.catalog_expansion import CPU_LADDER_URL, DIY_SOURCE_URL, GPU_LADDER_URL
from app.features.catalog_sync.service import find_catalog_part
from app.features.products.taobao_mcp import fetch_taobao_offer
from app.features.products.zol_public import (
    ZolProductSnapshot,
    fetch_zol_public_product,
    validate_zol_product_url,
)

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
        "是否支持核显": "integrated_graphics",
        "核显": "integrated_graphics",
        "功率": "tdp",
        "设计功耗": "tdp",
        "最大睿频功耗": "max_turbo_power",
        "制程工艺": "process",
        "架构": "architecture",
        "上市年份": "launch_year",
        "上市日期": "launch_date",
        "内存支持": "memory_types",
        "适用CPU接口": "socket",
        "CPU插槽": "socket",
        "板型": "form_factor",
        "内存类型": "memory_type",
        "最大内存容量": "max_memory",
        "内存插槽数量": "memory_slots",
        "内存插槽": "memory_slots",
        "最高内存频率": "max_memory_speed",
        "芯片组": "chipset",
        "显卡插槽": "gpu_slot",
        "PCIe版本": "pcie_version",
        "支持PCIe协议": "pcie_version",
        "PCIe接口": "pcie_slot",
        "M.2接口数量": "m2_slots",
        "M.2插槽": "m2_slots",
        "SATA接口数量": "sata_ports",
        "无线标准": "wifi",
        "Wi-Fi": "wifi",
        "蓝牙": "bluetooth",
        "有线网卡": "lan",
        "音频芯片": "audio_codec",
        "供电相数": "power_phase",
        "USB接口": "usb_ports",
        "USB-C接口": "usb_c",
        "主板供电接口": "motherboard_power_connector",
        "CPU供电接口": "cpu_power_connector",
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
        "整卡总功耗": "tgp",
        "显卡长度": "length_mm",
        "产品尺寸": "dimensions",
        "插槽": "slot_count",
        "内存频率": "speed_mts",
        "时序": "timings",
        "工作电压": "voltage",
        "传输协议": "protocol",
        "主控": "controller",
        "闪存类型": "nand",
        "顺序读取": "seq_read_mb_s",
        "顺序写入": "seq_write_mb_s",
        "写入寿命": "tbw",
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
    for raw_label, raw_value in re.findall(
        r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", page, re.I | re.S
    ):
        label, value = _plain_text(raw_label), _plain_text(raw_value)
        if label and value:
            normalized_label = re.sub(r"\s+", "", label)
            key = label_map.get(label) or label_map.get(normalized_label) or f"jd_{label}"
            parameters[key] = value

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
                    normalized_label = re.sub(r"\s+", "", label)
                    key = label_map.get(label) or label_map.get(normalized_label) or f"jd_{label}"
                    parameters[key] = str(item["value"])
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


def platform_search_offers(part: Part) -> list[Offer]:
    """返回平台搜索入口，不从目录参考价推导平台金额。"""

    keyword = quote(part.name)
    rows = (
        (
            "jd",
            "京东平台搜索入口",
            f"https://search.jd.com/Search?keyword={keyword}",
        ),
        (
            "pdd",
            "拼多多平台搜索入口",
            f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}",
        ),
    )
    return [
        Offer(
            part_id=part.id,
            source=source,
            platform=platform,
            status="待联网",
            url=url,
            is_live=False,
        )
        for platform, source, url in rows
    ]


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


def _zol_price_summary(snapshot: ZolProductSnapshot) -> str:
    if snapshot.reference_price is None:
        return "待确认"
    return f"为 ¥{snapshot.reference_price:.0f}"


async def get_product_detail(part_id: str, settings: Settings | None = None) -> ProductDetail:
    configured = settings or get_settings()
    part = find_catalog_part(part_id)
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
    zol_snapshot: ZolProductSnapshot | None = None
    zol_url = configured.zol_product_urls.get(part_id)
    if not zol_url and part.url:
        try:
            zol_url = validate_zol_product_url(part.url)
        except ValueError:
            zol_url = None
    if not configured.zol_public_fetch_enabled:
        sources.append(
            DataSourceStatus(
                provider="中关村在线公开参数页",
                kind="parameters",
                status="disabled",
                note="公开参数页解析已关闭；启用后只读取明确绑定的数字产品页。",
                url=zol_url,
            )
        )
    elif not zol_url:
        sources.append(
            DataSourceStatus(
                provider="中关村在线公开参数页",
                kind="parameters",
                status="unconfigured",
                note="当前型号没有绑定 ZOL 数字产品参数页，继续使用结构化目录。",
            )
        )
    else:
        try:
            zol_snapshot = await fetch_zol_public_product(zol_url, configured)
            result_part.specs.update(zol_snapshot.parameters)
            if zol_snapshot.reference_price is not None:
                result_part.price = zol_snapshot.reference_price
                result_part.source = "ZOL公开详情页参考价"
                result_part.data_updated_at = captured.date().isoformat()
            sources.append(
                DataSourceStatus(
                    provider="中关村在线公开参数页",
                    kind="parameters",
                    status="public_reference",
                    note=(
                        f"已读取公开 HTML，解析到 {len(zol_snapshot.parameters)} 个参数字段；"
                        "页面报价仅作为公开参考价。"
                    ),
                    url=zol_url,
                    captured_at=captured,
                )
            )
            evidence.append(
                Evidence(
                    source="中关村在线公开参数页",
                    title=zol_snapshot.title or part.name,
                    url=zol_url,
                    summary=f"解析到 {len(zol_snapshot.parameters)} 个参数字段，"
                    f"公开参考价{_zol_price_summary(zol_snapshot)}。",
                    confidence="medium",
                )
            )
        except (httpx.HTTPError, ValueError) as exc:
            sources.append(
                DataSourceStatus(
                    provider="中关村在线公开参数页",
                    kind="parameters",
                    status="unavailable",
                    note=f"公开页读取失败，已回退结构化目录：{str(exc)[:100]}",
                    url=zol_url,
                    captured_at=captured,
                )
            )
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
    offers = platform_search_offers(result_part)
    if zol_snapshot and zol_snapshot.jd_price is not None:
        jd_offer = Offer(
            part_id=result_part.id,
            price=zol_snapshot.jd_price,
            source="中关村在线品牌电商公开信息",
            platform="jd",
            discount_price=zol_snapshot.jd_price,
            landed_price=zol_snapshot.jd_price,
            seller=zol_snapshot.jd_seller or "京东商城",
            status="公开参考价",
            url=zol_snapshot.jd_url or zol_url,
            captured_at=captured,
            is_live=False,
        )
        offers = [offer for offer in offers if offer.platform != "jd"]
        offers.insert(0, jd_offer)
        sources.append(
            DataSourceStatus(
                provider="京东",
                kind="price",
                status="public_reference",
                note="金额来自 ZOL 页面展示的京东品牌电商公开参考价，不代表实时成交价。",
                url=zol_snapshot.jd_url or zol_url,
                captured_at=captured,
            )
        )
    else:
        sources.append(
            DataSourceStatus(
                provider="京东",
                kind="price",
                status="unavailable",
                note="未取得可核验的授权报价；已保留京东搜索入口，不显示由目录价推导的金额。",
                url=offers[0].url if offers and offers[0].platform == "jd" else None,
            )
        )
    pdd_offer = next((offer for offer in offers if offer.platform == "pdd"), None)
    sources.append(
        DataSourceStatus(
            provider="拼多多",
            kind="price",
            status="unavailable",
            note="未取得可核验的授权报价；已保留拼多多搜索入口，不显示示例金额。",
            url=pdd_offer.url if pdd_offer else None,
        )
    )
    taobao = await fetch_taobao_offer(result_part, configured)
    if taobao.parameters:
        result_part.specs.update(taobao.parameters)
        evidence.append(
            Evidence(
                source="淘宝 MCP",
                title=taobao.title or result_part.name,
                url=taobao.offer.url if taobao.offer else None,
                summary=(
                    f"已读取淘宝/天猫商品的 {len(taobao.parameters)} 个可用参数；"
                    "实时价仍可能随地区、库存和活动变化。"
                ),
                confidence="medium",
            )
        )
    sources.append(
        DataSourceStatus(
            provider="淘宝 MCP",
            kind="price",
            status=taobao.status,
            note=taobao.note,
            url=taobao.offer.url if taobao.offer else None,
            captured_at=taobao.offer.captured_at if taobao.offer else None,
        )
    )
    if taobao.offer is not None:
        offers.append(taobao.offer)
    return ProductDetail(
        part=result_part,
        offers=offers,
        evidence=evidence,
        sources=sources,
    )
