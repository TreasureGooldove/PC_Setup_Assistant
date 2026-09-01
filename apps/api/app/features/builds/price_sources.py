"""商品报价来源的统一字段与启用检查。

这里只做数据标准化和配置判断，不在服务端绕过验证码或批量抓取页面。
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from os import environ
from typing import Any

from app.domain import Offer, PartCategory

PLATFORM_ENV: dict[str, tuple[str, ...]] = {
    "jd": ("JD_APP_KEY", "JD_APP_SECRET", "JD_PID"),
    "pdd": ("PDD_CLIENT_ID", "PDD_CLIENT_SECRET", "PDD_PID"),
    "taobao": ("TAOBAO_APP_KEY", "TAOBAO_APP_SECRET", "TAOBAO_ADZONE_ID"),
}

PLATFORM_LABELS = {
    "jd": "京东联盟",
    "pdd": "拼多多多多客",
    "taobao": "淘宝联盟",
}


def _value(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        current: Any = payload
        for segment in key.split("."):
            if not isinstance(current, Mapping) or segment not in current:
                current = None
                break
            current = current[segment]
        if current not in (None, ""):
            return current
    return None


def _money(value: Any, unit: str) -> float | None:
    if value in (None, ""):
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(value).replace(",", ""))
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    if unit == "fen":
        amount /= 100
    return float(max(Decimal("0"), amount).quantize(Decimal("0.01")))


def _platform_prices(platform: str, payload: Mapping[str, Any]) -> tuple[Any, Any, Any, str]:
    if platform == "pdd":
        return (
            _value(payload, "min_normal_price", "normal_price"),
            _value(payload, "min_group_price", "group_price"),
            _value(payload, "coupon_discount"),
            "fen",
        )
    if platform == "taobao":
        return (
            _value(payload, "reserve_price", "original_price"),
            _value(payload, "zk_final_price", "discount_price", "final_price", "price"),
            _value(payload, "coupon_amount", "coupon_discount"),
            "yuan",
        )
    return (
        _value(payload, "priceInfo.price", "price", "list_price"),
        _value(payload, "discount_price", "coupon_price", "priceInfo.price"),
        _value(payload, "coupon_amount", "coupon_discount"),
        "yuan",
    )


def normalize_offer(
    part_id: str,
    platform: str,
    payload: Mapping[str, Any],
    *,
    captured_at: datetime | None = None,
    price_unit: str | None = None,
) -> Offer | None:
    """把平台返回的商品字段转为内部报价。

    PDD 的联盟价格字段按分处理；JD/Taobao 默认按元处理，调用方可用
    ``price_unit`` 覆盖。最终推荐金额会优先使用券后预估到手价，但会保留原始字段。
    """

    platform = platform.lower().strip()
    if platform not in PLATFORM_LABELS:
        raise ValueError(f"不支持的报价平台：{platform}")
    list_raw, discount_raw, coupon_raw, default_unit = _platform_prices(platform, payload)
    unit = price_unit or default_unit
    list_price = _money(list_raw, unit)
    discount_price = _money(discount_raw, unit)
    coupon = _money(coupon_raw, unit)
    base_price = discount_price or list_price
    if base_price is None:
        return None
    landed_price = max(0, round(base_price - (coupon or 0), 2))
    coupon_note = f"优惠约 ¥{coupon:.2f}" if coupon else None
    return Offer(
        part_id=part_id,
        price=landed_price,
        source=PLATFORM_LABELS[platform],
        platform=platform,
        sku=str(_value(payload, "sku_id", "goods_sign", "item_id"))
        if _value(payload, "sku_id", "goods_sign", "item_id") is not None
        else None,
        list_price=list_price,
        discount_price=discount_price,
        landed_price=landed_price,
        seller=_value(
            payload,
            "mall_name",
            "shop_title",
            "shop_name",
            "store_name",
            "seller_nick",
        ),
        region=_value(payload, "provcity", "region"),
        coupon_note=coupon_note,
        status="活动价" if coupon else "参考价",
        url=_value(payload, "click_url", "coupon_share_url", "material_url", "url"),
        captured_at=captured_at or datetime.now(UTC),
    )


def enabled_marketplaces(env: Mapping[str, str] | None = None) -> list[str]:
    """只返回凭证完整的平台，缺少任何字段都保持停用。"""

    values = env if env is not None else environ
    return [
        platform
        for platform, required in PLATFORM_ENV.items()
        if all(values.get(key, "").strip() for key in required)
    ]


class ConfiguredMarketplaceProvider:
    """后续接入官方/联盟 SDK 的统一占位。

    适配器拿到的原始结果应先经过 :func:`normalize_offer`，再进入推荐排序。
    """

    def __init__(self, platform: str, env: Mapping[str, str] | None = None) -> None:
        if platform not in PLATFORM_ENV:
            raise ValueError(f"不支持的报价平台：{platform}")
        self.platform = platform
        self._env = env if env is not None else environ
        self.name = PLATFORM_LABELS[platform]

    @property
    def enabled(self) -> bool:
        return platform_is_enabled(self.platform, self._env)

    async def search(
        self,
        category: PartCategory,
        query: str = "",
    ) -> list[Offer]:
        del category, query
        return []


def platform_is_enabled(platform: str, env: Mapping[str, str] | None = None) -> bool:
    values = env if env is not None else environ
    return platform in enabled_marketplaces(values)
