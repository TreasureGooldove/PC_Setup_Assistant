"""中关村在线公开参数页的受控解析器。

这里只读取用户明确提供或目录明确绑定的 ``detail.zol.com.cn`` 参数页，
不使用登录态、不跟随重定向，也不尝试绕过验证码、访问控制或反爬机制。
页面上的报价按“公开参考价”处理，不能替代平台实时成交价。
"""

from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import Settings

MAX_ZOL_HTML_BYTES = 2_000_000
ZOL_PRODUCT_PATH = re.compile(r"/\d+/\d+/param\.shtml")


@dataclass(frozen=True)
class ZolProductSnapshot:
    title: str | None
    parameters: dict[str, str | int]
    reference_price: float | None
    jd_price: float | None
    jd_url: str | None
    jd_seller: str | None


def validate_zol_product_url(url: str) -> str:
    """只接受 ZOL 的数字产品参数页。"""

    value = url.strip()
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "detail.zol.com.cn"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or not ZOL_PRODUCT_PATH.fullmatch(parsed.path)
    ):
        raise ValueError(
            "中关村在线参数页必须是 https://detail.zol.com.cn/<数字>/<数字>/param.shtml"
        )
    return value


def _plain_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_module.unescape(text)).strip()


def _clean_value(value: str) -> str | None:
    cleaned = _plain_text(value)
    cleaned = re.sub(r"(?:纠错|>>|＞＞)\s*$", "", cleaned).strip(" ：:")
    if not cleaned or cleaned in {"-", "--", "暂无", "暂无数据", "未提供"}:
        return None
    return cleaned


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).strip(" ：:")


def _number(value: str) -> int | None:
    match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
    return int(float(match.group(0))) if match else None


def _canonical_value(key: str, value: str) -> str | int:
    if key == "socket":
        normalized = re.sub(r"\s+", "", value)
        return normalized.replace("CPU", "")
    if key == "form_factor":
        normalized = value.casefold().replace(" ", "")
        if "mini-itx" in normalized or "miniitx" in normalized:
            return "Mini-ITX"
        if "micro-atx" in normalized or "microatx" in normalized or "matx" in normalized:
            return "mATX"
        if normalized.startswith("atx"):
            return "ATX"
    if key == "memory_type":
        has_ddr4 = "DDR4" in value.upper()
        has_ddr5 = "DDR5" in value.upper()
        if has_ddr4 and has_ddr5:
            return "DDR4 / DDR5"
        if has_ddr4:
            return "DDR4"
        if has_ddr5:
            return "DDR5"
    if key in {"memory_slots", "m2_slots", "sata_ports"}:
        return _number(value) or value
    return value


_PARAMETER_ALIASES = {
    "品牌": "brand_name",
    "型号": "model",
    "商品名称": "product_name",
    "主芯片组": "chipset",
    "芯片组": "chipset",
    "CPU插槽": "socket",
    "适用CPU接口": "socket",
    "内存类型": "memory_type",
    "最大内存容量": "max_memory",
    "内存插槽数量": "memory_slots",
    "内存插槽": "memory_slots",
    "主板板型": "form_factor",
    "板型": "form_factor",
    "外形尺寸": "dimensions",
    "产品尺寸": "dimensions",
    "PCI-E标准": "pcie_version",
    "PCIe标准": "pcie_version",
    "PCI-E插槽": "pcie_slots",
    "PCIe插槽": "pcie_slots",
    "PCI-E X16插槽": "pcie_x16_slots",
    "PCI-E X1插槽": "pcie_x1_slots",
    "显卡插槽": "gpu_slot",
    "M.2接口数量": "m2_slots",
    "M.2插槽数量": "m2_slots",
    "SATA接口数量": "sata_ports",
    "存储接口": "storage_interfaces",
    "USB接口": "usb_ports",
    "USB接口（背板）": "usb_ports",
    "USB接口（主板背板）": "usb_ports",
    "USB（背板）": "usb_ports",
    "USB(背板）": "usb_ports",
    "USB(背板)": "usb_ports",
    "USB（内置）": "usb_header",
    "USB(内置）": "usb_header",
    "USB(内置)": "usb_header",
    "CPU类型": "cpu_type",
    "内存描述": "memory_description",
    "芯片组描述": "chipset_description",
    "其它接口": "other_interfaces",
    "其他接口": "other_interfaces",
    "I/O接口": "outputs",
    "视频接口": "outputs",
    "音频芯片": "audio_codec",
    "网卡芯片": "lan",
    "有线网卡": "lan",
    "板载Wi-Fi": "wifi",
    "无线标准": "wifi",
    "蓝牙": "bluetooth",
    "电源插口": "motherboard_power_connector",
    "电源接口": "motherboard_power_connector",
    "主板供电接口": "motherboard_power_connector",
    "CPU供电接口": "cpu_power_connector",
}

_COMPACT_PARAMETER_ALIASES = {_compact(label): key for label, key in _PARAMETER_ALIASES.items()}


def _add_parameter(parameters: dict[str, str | int], label: str, raw_value: str) -> None:
    value = _clean_value(raw_value)
    if not value:
        return
    compact_label = _compact(label)
    key = _COMPACT_PARAMETER_ALIASES.get(compact_label) or f"zol_{compact_label}"
    normalized_value = _canonical_value(key, value)
    parameters[key] = normalized_value
    if key == "max_memory":
        capacity = _number(value)
        if capacity is not None:
            parameters["max_memory_gb"] = capacity
    if key == "storage_interfaces":
        m2_match = re.search(r"(\d+)\s*[×x*]\s*M\.?2", value, re.IGNORECASE)
        sata_match = re.search(r"(\d+)\s*[×x*]\s*SATA", value, re.IGNORECASE)
        if m2_match:
            parameters["m2_slots"] = int(m2_match.group(1))
        if sata_match:
            parameters["sata_ports"] = int(sata_match.group(1))
    if key == "memory_description" and "双通道" in value:
        parameters["memory_channels"] = "双通道"


def _parse_parameters(page: str) -> dict[str, str | int]:
    parameters: dict[str, str | int] = {}
    for raw_value in re.findall(r"<p\b[^>]*>(.*?)</p>", page, re.IGNORECASE | re.DOTALL):
        plain = _plain_text(raw_value)
        match = re.match(r"([^：:]{1,40})\s*[：:]\s*(.+)", plain)
        if match:
            label, value = match.group(1), match.group(2)
            title_match = re.search(r"\btitle=[\"']([^\"']*)[\"']", raw_value, re.IGNORECASE)
            data_values = re.findall(
                r"\bdata-text=[\"']([^\"']+)[\"']", raw_value, re.IGNORECASE
            )
            candidates = [value]
            if title_match and title_match.group(1).strip():
                candidates.append(title_match.group(1))
            candidates.extend(data_values)
            _add_parameter(parameters, label, max(candidates, key=len))

    for raw_row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", page, re.IGNORECASE | re.DOTALL):
        header = re.search(r"<th\b[^>]*>(.*?)</th>", raw_row, re.IGNORECASE | re.DOTALL)
        value = re.search(r"<td\b[^>]*>(.*?)</td>", raw_row, re.IGNORECASE | re.DOTALL)
        if not header or not value:
            continue
        label = _plain_text(header.group(1))
        label = re.sub(r"(?:纠错|>>|＞＞)\s*$", "", label).strip()
        if label:
            _add_parameter(parameters, label, value.group(1))
    return parameters


def _money(fragment: str) -> float | None:
    text = _plain_text(fragment)
    match = re.search(r"(?:￥|¥|&yen;)?\s*([\d,]+(?:\.\d+)?)", text)
    return float(match.group(1).replace(",", "")) if match else None


def _reference_price(page: str) -> float | None:
    matches = re.findall(
        r"<div\b[^>]*class=[\"'][^\"']*goods-card__price[^\"']*[\"'][^>]*>(.*?)</div>",
        page,
        re.IGNORECASE | re.DOTALL,
    )
    for fragment in matches:
        price = _money(fragment)
        if price is not None:
            return price
    return None


def _jd_offer(page: str) -> tuple[float | None, str | None, str | None]:
    module_match = re.search(
        r"<div\b[^>]*id=[\"']brand-seller-jd[\"'][^>]*>(.*?)(?=<div\b[^>]*id=[\"']brand-seller-|</section>|$)",
        page,
        re.IGNORECASE | re.DOTALL,
    )
    module = module_match.group(1) if module_match else ""
    if not module:
        module_match = re.search(
            r"<a\b[^>]*class=[\"'][^\"']*goods-card-jd[^\"']*[\"'][^>]*>(.*?)</a>",
            page,
            re.IGNORECASE | re.DOTALL,
        )
        module = module_match.group(0) if module_match else ""
    if not module:
        return None, None, None
    price_match = re.search(
        r"class=[\"'][^\"']*price[^\"']*[\"'][^>]*>(.*?)</(?:span|div)>",
        module,
        re.IGNORECASE | re.DOTALL,
    )
    price = _money(price_match.group(1)) if price_match else _money(module)
    url_match = re.search(
        r"href=[\"'](https://union-click\.jd\.com/[^\"']+)",
        module,
        re.IGNORECASE,
    )
    seller = "京东商城" if "京东商城" in _plain_text(module) else None
    return price, url_match.group(1) if url_match else None, seller


def parse_zol_product_html(page: str) -> ZolProductSnapshot:
    """从 ZOL 参数页提取标题、完整可见参数和公开参考报价。"""

    title_match = re.search(r"<title\b[^>]*>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    title = _clean_value(title_match.group(1)) if title_match else None
    parameters = _parse_parameters(page)
    reference_price = _reference_price(page)
    jd_price, jd_url, jd_seller = _jd_offer(page)
    return ZolProductSnapshot(
        title=title,
        parameters=parameters,
        reference_price=reference_price,
        jd_price=jd_price,
        jd_url=jd_url,
        jd_seller=jd_seller,
    )


async def fetch_zol_public_product(url: str, settings: Settings) -> ZolProductSnapshot:
    safe_url = validate_zol_product_url(url)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(settings.catalog_sync_timeout_seconds),
        follow_redirects=False,
        trust_env=False,
        headers={"User-Agent": "PC-Setup-Assistant/0.1 public-product-metadata"},
    ) as client:
        response = await client.get(safe_url)
    response.raise_for_status()
    if response.is_redirect:
        raise ValueError("中关村在线参数页发生重定向，已停止解析")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ValueError("中关村在线参数页未返回 HTML")
    if len(response.content) > MAX_ZOL_HTML_BYTES:
        raise ValueError("中关村在线参数页超过解析大小限制")
    encoding = response.encoding or "gb18030"
    return parse_zol_product_html(response.content.decode(encoding, errors="replace"))
