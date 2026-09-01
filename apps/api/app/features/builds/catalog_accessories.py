from __future__ import annotations

# ruff: noqa: E501 -- 目录元组保持单行，便于按产品核对与维护。
from typing import Any

from app.domain import Part, PartCategory

DIY_SOURCE_URL = "https://diy.zol.com.cn/"


def _part(
    item_id: str,
    category: PartCategory,
    name: str,
    brand: str,
    price: float,
    specs: dict[str, Any],
    *,
    power_w: int = 0,
    summary: str,
) -> Part:
    return Part(
        id=item_id,
        category=category,
        name=name,
        brand=brand,
        price=price,
        source="ZOL DIY 结构参考 · Fixture参考价",
        url=DIY_SOURCE_URL,
        specs=specs,
        power_w=power_w,
        summary=summary,
        advantages=["型号与关键规格已结构化，可参与筛选和装机检查。"],
        cautions=["价格为离线参考，购买前请在商品页面核价。"],
        data_updated_at="2026-08-31",
    )


def accessory_parts() -> list[Part]:
    """为非核心分类提供足量、可复现且带兼容字段的候选。"""

    memory_rows = [
        (
            "ram-kingston-fury-d4-32",
            "FURY Beast DDR4 3200 32GB套装",
            "金士顿",
            459,
            "DDR4",
            32,
            3200,
        ),
        (
            "ram-corsair-vengeance-d4-32",
            "VENGEANCE LPX DDR4 3600 32GB套装",
            "海盗船",
            529,
            "DDR4",
            32,
            3600,
        ),
        ("ram-gloway-d4-32", "天策 DDR4 3600 32GB套装", "光威", 389, "DDR4", 32, 3600),
        (
            "ram-kingston-fury-d5-32",
            "FURY Beast DDR5 6000 32GB套装",
            "金士顿",
            799,
            "DDR5",
            32,
            6000,
        ),
        ("ram-gskill-trident-d5-32", "焰锋戟 DDR5 6000 32GB套装", "芝奇", 999, "DDR5", 32, 6000),
        (
            "ram-corsair-dominator-d5-32",
            "DOMINATOR DDR5 6400 32GB套装",
            "海盗船",
            1299,
            "DDR5",
            32,
            6400,
        ),
        ("ram-crucial-pro-d5-32", "Pro DDR5 6000 32GB套装", "英睿达", 729, "DDR5", 32, 6000),
        (
            "ram-predator-vesta-d5-32",
            "Vesta II DDR5 6800 32GB套装",
            "宏碁掠夺者",
            899,
            "DDR5",
            32,
            6800,
        ),
        ("ram-teamgroup-d5-48", "T-CREATE DDR5 6400 48GB套装", "十铨", 1199, "DDR5", 48, 6400),
        ("ram-asgard-d5-64", "博拉琪 DDR5 6000 64GB套装", "阿斯加特", 1399, "DDR5", 64, 6000),
    ]
    memory = [
        _part(
            item_id,
            PartCategory.MEMORY,
            name,
            brand,
            price,
            {
                "memory_type": memory_type,
                "capacity_gb": capacity,
                "speed_mts": speed,
                "kit": "2条套装",
                "catalog_kind": memory_type,
            },
            summary=f"{capacity}GB 双通道套装，速率 {speed}MT/s。",
        )
        for item_id, name, brand, price, memory_type, capacity, speed in memory_rows
    ]

    storage_rows = [
        (
            "ssd-samsung-990pro-1t",
            "990 PRO 1TB PCIe 4.0 固态硬盘",
            "三星",
            799,
            1024,
            "PCIe 4.0",
            "M.2",
        ),
        (
            "ssd-wd-sn850x-2t",
            "WD_BLACK SN850X 2TB 固态硬盘",
            "西部数据",
            1199,
            2048,
            "PCIe 4.0",
            "M.2",
        ),
        (
            "ssd-solidigm-p44pro-2t",
            "P44 Pro 2TB 固态硬盘",
            "Solidigm",
            1099,
            2048,
            "PCIe 4.0",
            "M.2",
        ),
        ("ssd-crucial-t500-1t", "T500 1TB 固态硬盘", "英睿达", 649, 1024, "PCIe 4.0", "M.2"),
        ("ssd-lexar-nm790-2t", "NM790 2TB 固态硬盘", "雷克沙", 899, 2048, "PCIe 4.0", "M.2"),
        ("ssd-kingston-kc3000-2t", "KC3000 2TB 固态硬盘", "金士顿", 1099, 2048, "PCIe 4.0", "M.2"),
        ("ssd-zhitai-7100-2t", "TiPlus7100 2TB 固态硬盘", "致态", 999, 2048, "PCIe 4.0", "M.2"),
        ("ssd-predator-gm7-1t", "GM7 1TB 固态硬盘", "宏碁掠夺者", 499, 1024, "PCIe 4.0", "M.2"),
        ("ssd-fanxiang-s790-4t", "S790 4TB 固态硬盘", "梵想", 1599, 4096, "PCIe 4.0", "M.2"),
        (
            "ssd-wd-blue-sa510-1t",
            "Blue SA510 1TB SATA 固态硬盘",
            "西部数据",
            469,
            1024,
            "SATA 6Gb/s",
            "SATA",
        ),
    ]
    storage = [
        _part(
            item_id,
            PartCategory.STORAGE,
            name,
            brand,
            price,
            {
                "capacity_gb": capacity,
                "interface": interface,
                "connector": connector,
                "catalog_kind": f"{capacity // 1024}TB" if capacity >= 1024 else f"{capacity}GB",
            },
            summary=f"{capacity // 1024 if capacity >= 1024 else capacity}{'TB' if capacity >= 1024 else 'GB'} {interface} 存储。",
        )
        for item_id, name, brand, price, capacity, interface, connector in storage_rows
    ]

    psu_rows = [
        ("psu-corsair-rm650e", "RM650e 650W 金牌全模组电源", "海盗船", 699, 650, 3, True),
        ("psu-seasonic-focus750", "FOCUS GX-750 750W 金牌全模组电源", "海韵", 899, 750, 3, True),
        ("psu-msi-a750gl", "MAG A750GL PCIE5 750W 金牌全模组", "微星", 699, 750, 3, True),
        ("psu-antec-ne850", "NE850 850W 金牌全模组电源", "安钛克", 799, 850, 4, True),
        ("psu-corsair-rm850e", "RM850e 850W 金牌全模组电源", "海盗船", 899, 850, 4, True),
        ("psu-superflower-850", "LEADEX VII 850W 金牌全模组", "振华", 999, 850, 4, True),
        ("psu-coolermaster-v850", "V850 GOLD i 850W 金牌全模组", "酷冷至尊", 1099, 850, 4, True),
        ("psu-seasonic-vertex1000", "VERTEX GX-1000 1000W 金牌全模组", "海韵", 1499, 1000, 5, True),
        ("psu-corsair-rm1000x", "RM1000x SHIFT 1000W 金牌全模组", "海盗船", 1399, 1000, 5, True),
        ("psu-greatwall-1250", "巨龙 1250W 白金全模组电源", "长城", 1599, 1250, 6, True),
    ]
    psus = [
        _part(
            item_id,
            PartCategory.PSU,
            name,
            brand,
            price,
            {
                "wattage": wattage,
                "rating": "Platinum" if wattage >= 1250 else "Gold",
                "pcie_8pin_count": pcie_count,
                "atx_3_0": atx3,
                "twelve_vhpwr": atx3,
                "modular": "全模组",
                "catalog_kind": f"{wattage}W",
            },
            summary=f"额定 {wattage}W，支持现代独显供电规格。",
        )
        for item_id, name, brand, price, wattage, pcie_count, atx3 in psu_rows
    ]

    cooling_rows = [
        ("cooler-thermalright-ax120", "Assassin X 120 Refined SE", "利民", 79, "air", 148, 0, 180),
        ("cooler-deepcool-ak400", "AK400 单塔风冷散热器", "九州风神", 139, "air", 155, 0, 220),
        (
            "cooler-thermalright-pa120se",
            "Peerless Assassin 120 SE 双塔风冷",
            "利民",
            169,
            "air",
            155,
            0,
            265,
        ),
        ("cooler-deepcool-ak620", "AK620 双塔风冷散热器", "九州风神", 349, "air", 160, 0, 280),
        ("cooler-noctua-nhd15", "NH-D15 G2 双塔风冷散热器", "猫头鹰", 1099, "air", 168, 0, 300),
        (
            "cooler-coolermaster-ml240",
            "冰神 B240 一体式水冷",
            "酷冷至尊",
            499,
            "water",
            0,
            240,
            280,
        ),
        (
            "cooler-deepcool-ls520",
            "冰堡垒 LS520 240 一体式水冷",
            "九州风神",
            599,
            "water",
            0,
            240,
            300,
        ),
        (
            "cooler-thermalright-fm360",
            "Frozen Magic 360 一体式水冷",
            "利民",
            499,
            "water",
            0,
            360,
            330,
        ),
        ("cooler-valkyrie-b360", "B360 ARGB 一体式水冷", "瓦尔基里", 599, "water", 0, 360, 350),
        (
            "cooler-lianli-galahad360",
            "极圈 II Trinity 360 一体式水冷",
            "联力",
            1099,
            "water",
            0,
            360,
            350,
        ),
        (
            "cooler-corsair-h150i",
            "iCUE H150i ELITE 360 一体式水冷",
            "海盗船",
            1299,
            "water",
            0,
            360,
            350,
        ),
        (
            "cooler-asus-ryujin360",
            "ROG 龙神 III 360 ARGB 一体式水冷",
            "华硕",
            2699,
            "water",
            0,
            360,
            380,
        ),
    ]
    cooling = [
        _part(
            item_id,
            PartCategory.COOLING,
            name,
            brand,
            price,
            {
                "type": cooling_type,
                "height_mm": height or None,
                "radiator_mm": radiator or None,
                "capacity_w": capacity,
                "supported_sockets": ["AM5", "LGA1700", "LGA1851"],
                "catalog_kind": "风冷散热器" if cooling_type == "air" else "水冷散热器",
            },
            summary=(
                f"{height}mm 高风冷，标称解热能力约 {capacity}W。"
                if cooling_type == "air"
                else f"{radiator}mm 一体式水冷，标称解热能力约 {capacity}W。"
            ),
        )
        for item_id, name, brand, price, cooling_type, height, radiator, capacity in cooling_rows
    ]

    case_rows = [
        ("case-jonsbo-d31", "D31 MESH mATX 机箱", "乔思伯", 399, "mATX", 400, 168, 360),
        ("case-lianli-a3", "A3-mATX 紧凑型机箱", "联力", 499, "mATX", 415, 165, 360),
        ("case-sama-quzao", "趣造 2 mATX 机箱", "先马", 329, "mATX", 350, 165, 240),
        ("case-asus-ap201", "Prime AP201 mATX 机箱", "华硕", 499, "mATX", 338, 170, 360),
        ("case-nzxt-h5flow", "H5 Flow ATX 机箱", "NZXT", 599, "ATX", 365, 165, 280),
        ("case-corsair-4000d", "4000D AIRFLOW ATX 机箱", "海盗船", 699, "ATX", 360, 170, 360),
        ("case-lianli-lancool216", "LANCOOL 216 ATX 机箱", "联力", 699, "ATX", 392, 180, 360),
        ("case-fractal-north", "North ATX 木纹机箱", "Fractal Design", 1199, "ATX", 355, 170, 360),
        (
            "case-nr200p",
            "MasterBox NR200P Mini-ITX 机箱",
            "酷冷至尊",
            599,
            "Mini-ITX",
            330,
            155,
            280,
        ),
        ("case-jonsbo-n2", "N2 Mini-ITX 小型机箱", "乔思伯", 699, "Mini-ITX", 260, 65, 120),
    ]
    cases = [
        _part(
            item_id,
            PartCategory.CASE,
            name,
            brand,
            price,
            {
                "form_factor": form_factor,
                "supported_form_factors": (
                    ["Mini-ITX"]
                    if form_factor == "Mini-ITX"
                    else ["mATX", "Mini-ITX"]
                    if form_factor == "mATX"
                    else ["ATX", "mATX", "Mini-ITX"]
                ),
                "gpu_length_mm": gpu_length,
                "cooler_height_mm": cooler_height,
                "radiator_mm": radiator,
                "catalog_kind": form_factor,
            },
            summary=f"{form_factor} 机箱，显卡限长 {gpu_length}mm。",
        )
        for item_id, name, brand, price, form_factor, gpu_length, cooler_height, radiator in case_rows
    ]

    return memory + storage + psus + cooling + cases
