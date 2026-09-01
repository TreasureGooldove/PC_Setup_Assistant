from __future__ import annotations

# ruff: noqa: E501 -- 目录元组保持单行，便于按产品核对与维护。
from typing import Any

from app.domain import Part, PartCategory

CPU_LADDER_URL = "https://cpu.zol.com.cn/soc/"
GPU_LADDER_URL = "https://vga.zol.com.cn/soc/"
DIY_SOURCE_URL = "https://diy.zol.com.cn/"


def _part(
    item_id: str,
    category: PartCategory,
    name: str,
    brand: str,
    price: float,
    specs: dict[str, Any],
    power_w: int = 0,
    *,
    summary: str = "",
) -> Part:
    return Part(
        id=item_id,
        category=category,
        name=name,
        brand=brand,
        price=price,
        source="规格结构参考：中关村在线；价格：Fixture参考价",
        url=(
            CPU_LADDER_URL
            if category == PartCategory.CPU
            else GPU_LADDER_URL
            if category == PartCategory.GPU
            else DIY_SOURCE_URL
        ),
        specs=specs,
        power_w=power_w,
        summary=summary,
        data_updated_at="2026-08-30",
    )


def expanded_parts() -> list[Part]:
    """扩展选配候选；价格是可复现示例，不表示实时成交价。"""

    cpu_rows: list[tuple[str, str, str, float, str, int, str, str, str]] = [
        ("cpu-9950x3d", "Ryzen 9 9950X3D", "AMD", 5299, "AM5", 170, "16核32线程", "Zen 5", "DDR5"),
        ("cpu-9950x", "Ryzen 9 9950X", "AMD", 4299, "AM5", 170, "16核32线程", "Zen 5", "DDR5"),
        ("cpu-9800x3d", "Ryzen 7 9800X3D", "AMD", 3699, "AM5", 120, "8核16线程", "Zen 5", "DDR5"),
        ("cpu-9700x", "Ryzen 7 9700X", "AMD", 2299, "AM5", 65, "8核16线程", "Zen 5", "DDR5"),
        ("cpu-9600x", "Ryzen 5 9600X", "AMD", 1699, "AM5", 65, "6核12线程", "Zen 5", "DDR5"),
        ("cpu-7600", "Ryzen 5 7600", "AMD", 1199, "AM5", 65, "6核12线程", "Zen 4", "DDR5"),
        (
            "cpu-14900k",
            "Core i9-14900K",
            "Intel",
            3899,
            "LGA1700",
            253,
            "24核32线程",
            "Raptor Lake Refresh",
            "DDR4 / DDR5",
        ),
        (
            "cpu-14700kf",
            "Core i7-14700KF",
            "Intel",
            2599,
            "LGA1700",
            253,
            "20核28线程",
            "Raptor Lake Refresh",
            "DDR4 / DDR5",
        ),
        (
            "cpu-13600kf",
            "Core i5-13600KF",
            "Intel",
            1499,
            "LGA1700",
            181,
            "14核20线程",
            "Raptor Lake",
            "DDR4 / DDR5",
        ),
        (
            "cpu-12100f",
            "Core i3-12100F",
            "Intel",
            549,
            "LGA1700",
            89,
            "4核8线程",
            "Alder Lake",
            "DDR4 / DDR5",
        ),
        (
            "cpu-ultra9-285k",
            "Core Ultra 9 285K",
            "Intel",
            4299,
            "LGA1851",
            250,
            "24核24线程",
            "Arrow Lake",
            "DDR5",
        ),
        (
            "cpu-ultra7-265k",
            "Core Ultra 7 265K",
            "Intel",
            2799,
            "LGA1851",
            250,
            "20核20线程",
            "Arrow Lake",
            "DDR5",
        ),
        (
            "cpu-ultra5-245k",
            "Core Ultra 5 245K",
            "Intel",
            1899,
            "LGA1851",
            159,
            "14核14线程",
            "Arrow Lake",
            "DDR5",
        ),
    ]
    cpu_parts = [
        _part(
            item_id,
            PartCategory.CPU,
            name,
            brand,
            price,
            {
                "socket": socket,
                "tdp": power,
                "cores_threads": cores,
                "architecture": architecture,
                "memory_types": memory,
                "integrated_graphics": not name.endswith(("F", "KF")),
            },
            power,
            summary=f"{cores} {architecture} 桌面处理器，选入后会复核插槽、散热和电源余量。",
        )
        for item_id, name, brand, price, socket, power, cores, architecture, memory in cpu_rows
    ]

    gpu_rows: list[tuple[str, str, str, float, int, int, str]] = [
        ("gpu-5090d", "GeForce RTX 5090 D 32G", "NVIDIA", 19999, 575, 32, "12V-2x6"),
        ("gpu-5080", "GeForce RTX 5080 16G", "NVIDIA", 9999, 360, 16, "12V-2x6"),
        ("gpu-5070ti", "GeForce RTX 5070 Ti 16G", "NVIDIA", 6999, 300, 16, "12V-2x6"),
        ("gpu-5070", "GeForce RTX 5070 12G", "NVIDIA", 4999, 250, 12, "12V-2x6"),
        ("gpu-5060ti", "GeForce RTX 5060 Ti 16G", "NVIDIA", 3499, 180, 16, "1x8pin"),
        ("gpu-5060", "GeForce RTX 5060 8G", "NVIDIA", 2499, 145, 8, "1x8pin"),
        ("gpu-4090", "GeForce RTX 4090 24G", "NVIDIA", 14999, 450, 24, "12VHPWR"),
        ("gpu-4080s", "GeForce RTX 4080 SUPER 16G", "NVIDIA", 8499, 320, 16, "12VHPWR"),
        ("gpu-4070tis", "GeForce RTX 4070 Ti SUPER 16G", "NVIDIA", 5999, 285, 16, "12VHPWR"),
        ("gpu-4070", "GeForce RTX 4070 12G", "NVIDIA", 3899, 200, 12, "1x8pin"),
        ("gpu-4060", "GeForce RTX 4060 8G", "NVIDIA", 2199, 115, 8, "1x8pin"),
        ("gpu-rx9070xt", "Radeon RX 9070 XT 16G", "AMD", 5299, 304, 16, "2x8pin"),
        ("gpu-rx9070", "Radeon RX 9070 16G", "AMD", 4499, 220, 16, "2x8pin"),
        ("gpu-rx7900xtx", "Radeon RX 7900 XTX 24G", "AMD", 6899, 355, 24, "3x8pin"),
        ("gpu-rx7900xt", "Radeon RX 7900 XT 20G", "AMD", 5499, 315, 20, "3x8pin"),
        ("gpu-rx7700xt", "Radeon RX 7700 XT 12G", "AMD", 3299, 245, 12, "2x8pin"),
    ]
    gpu_parts = [
        _part(
            item_id,
            PartCategory.GPU,
            name,
            brand,
            price,
            {
                "vram_gb": vram,
                "length_mm": 338 if power >= 320 else 305 if power >= 220 else 270,
                "pcie_slot": "PCIe 5.0 x16"
                if item_id.startswith(("gpu-50", "gpu-rx90"))
                else "PCIe 4.0 x16",
                "power_connectors": [connector],
            },
            power,
            summary=f"{vram}GB 显存独立显卡，选入后会复核机箱限长、供电接口和电源余量。",
        )
        for item_id, name, brand, price, power, vram, connector in gpu_rows
    ]

    aib_gpu_rows: list[tuple[str, str, str, float, int, int, int, str, str]] = [
        (
            "gpu-asus-tuf-5060ti-o16g",
            "TUF RTX 5060 Ti O16G GAMING",
            "华硕 ASUS",
            6699,
            180,
            16,
            128,
            "GDDR7",
            "RTX 5060 Ti",
        ),
        (
            "gpu-gigabyte-5080-gaming-oc",
            "魔鹰 RTX 5080 Gaming OC 16G",
            "技嘉 GIGABYTE",
            14299,
            360,
            16,
            256,
            "GDDR7",
            "RTX 5080",
        ),
        (
            "gpu-xfx-rx6750gre",
            "RX 6750 GRE 海外版 12GB",
            "讯景 XFX",
            2699,
            250,
            12,
            192,
            "GDDR6",
            "RX 6750 GRE",
        ),
        (
            "gpu-asus-tuf-5070-o12g",
            "TUF RTX 5070 O12G GAMING",
            "华硕 ASUS",
            7699,
            250,
            12,
            192,
            "GDDR7",
            "RTX 5070",
        ),
        (
            "gpu-gigabyte-5070-gaming-oc",
            "魔鹰 RTX 5070 Gaming OC 12G",
            "技嘉 GIGABYTE",
            7699,
            250,
            12,
            192,
            "GDDR7",
            "RTX 5070",
        ),
        (
            "gpu-yeston-rx6800xt-sakura",
            "RX 6800 XT 16GD6 樱瞳花嫁纪念版",
            "盈通 YESTON",
            2899,
            300,
            16,
            256,
            "GDDR6",
            "RX 6800 XT",
        ),
        (
            "gpu-colorful-5070-ultra",
            "iGame RTX 5070 Ultra W OC 12GB",
            "七彩虹 COLORFUL",
            6599,
            250,
            12,
            192,
            "GDDR7",
            "RTX 5070",
        ),
        (
            "gpu-msi-5070-trio",
            "RTX 5070 GAMING TRIO OC 12G",
            "微星 MSI",
            6899,
            250,
            12,
            192,
            "GDDR7",
            "RTX 5070",
        ),
        (
            "gpu-maxsun-5060ti-icraft",
            "RTX 5060 Ti iCraft OC 16G",
            "铭瑄 MAXSUN",
            4299,
            180,
            16,
            128,
            "GDDR7",
            "RTX 5060 Ti",
        ),
        (
            "gpu-sapphire-9070xt-nitro",
            "RX 9070 XT NITRO+ 16G",
            "蓝宝石 SAPPHIRE",
            6499,
            330,
            16,
            256,
            "GDDR6",
            "RX 9070 XT",
        ),
        (
            "gpu-powercolor-9070-reaper",
            "RX 9070 Reaper 16G",
            "撼讯 POWERCOLOR",
            4999,
            220,
            16,
            256,
            "GDDR6",
            "RX 9070",
        ),
        (
            "gpu-zotac-5080-solid",
            "RTX 5080 SOLID OC 16G",
            "索泰 ZOTAC",
            12999,
            360,
            16,
            256,
            "GDDR7",
            "RTX 5080",
        ),
    ]
    aib_gpu_parts = [
        _part(
            item_id,
            PartCategory.GPU,
            name,
            brand,
            price,
            {
                "chipset": chipset,
                "vram_gb": vram,
                "memory_type": memory_type,
                "memory_bus_bit": memory_bus,
                "length_mm": 340 if power >= 320 else 320 if power >= 250 else 300,
                "pcie_slot": "PCIe 5.0 x16"
                if "50" in chipset or "90" in chipset
                else "PCIe 4.0 x16",
                "power_connectors": ["12V-2x6" if chipset.startswith("RTX 50") else "2x8pin"],
                "catalog_kind": chipset,
            },
            power,
            summary=f"{brand} 非公版 {chipset}，{vram}GB {memory_type}、{memory_bus}bit。",
        )
        for (
            item_id,
            name,
            brand,
            price,
            power,
            vram,
            memory_bus,
            memory_type,
            chipset,
        ) in aib_gpu_rows
    ]

    board_rows: list[tuple[str, str, str, float, dict[str, Any]]] = [
        (
            "mb-msi-x870e-carbon",
            "MPG X870E CARBON MAX WIFI 暗黑",
            "微星 MSI",
            3499,
            {
                "socket": "AM5",
                "chipset": "AMD X870E",
                "memory_type": "DDR5",
                "form_factor": "ATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 5,
                "sata_ports": 4,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 7",
                "power_phase": "22+2+1相",
                "rgb": "ARGB",
            },
        ),
        (
            "mb-asus-x870e-e",
            "ROG STRIX X870E-E GAMING WIFI",
            "华硕 ASUS",
            3299,
            {
                "socket": "AM5",
                "chipset": "AMD X870E",
                "memory_type": "DDR5",
                "form_factor": "ATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 5,
                "sata_ports": 4,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 7",
                "power_phase": "18+2+2相",
                "rgb": "ARGB",
            },
        ),
        (
            "mb-msi-b650m-mortar",
            "MAG B650M MORTAR WIFI 迫击炮",
            "微星 MSI",
            1199,
            {
                "socket": "AM5",
                "chipset": "AMD B650",
                "memory_type": "DDR5",
                "form_factor": "mATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 2,
                "sata_ports": 4,
                "gpu_slot": "PCIe 4.0 x16",
                "wifi": "Wi-Fi 6E",
                "power_phase": "12+2+1相",
                "rgb": "ARGB",
            },
        ),
        (
            "mb-asus-b650m-plus",
            "TUF GAMING B650M-PLUS WIFI",
            "华硕 ASUS",
            1299,
            {
                "socket": "AM5",
                "chipset": "AMD B650",
                "memory_type": "DDR5",
                "form_factor": "mATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 2,
                "sata_ports": 4,
                "gpu_slot": "PCIe 4.0 x16",
                "wifi": "Wi-Fi 6",
                "power_phase": "12+2+2相",
                "rgb": "Aura Sync",
            },
        ),
        (
            "mb-gigabyte-b650-aorus",
            "B650 AORUS ELITE AX V2",
            "技嘉 GIGABYTE",
            1399,
            {
                "socket": "AM5",
                "chipset": "AMD B650",
                "memory_type": "DDR5",
                "form_factor": "ATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 3,
                "sata_ports": 4,
                "gpu_slot": "PCIe 4.0 x16",
                "wifi": "Wi-Fi 6E",
                "power_phase": "12+2+2相",
                "rgb": "RGB Fusion",
            },
        ),
        (
            "mb-asus-b650e-i",
            "ROG STRIX B650E-I GAMING WIFI",
            "华硕 ASUS",
            1999,
            {
                "socket": "AM5",
                "chipset": "AMD B650E",
                "memory_type": "DDR5",
                "form_factor": "Mini-ITX",
                "max_memory_gb": 128,
                "memory_slots": 2,
                "m2_slots": 2,
                "sata_ports": 2,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 6E",
                "power_phase": "10+2相",
                "rgb": "Aura Sync",
            },
        ),
        (
            "mb-msi-z790-tomahawk",
            "MAG Z790 TOMAHAWK MAX WIFI",
            "微星 MSI",
            2199,
            {
                "socket": "LGA1700",
                "chipset": "Intel Z790",
                "memory_type": "DDR5",
                "form_factor": "ATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 4,
                "sata_ports": 8,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 7",
                "power_phase": "16+1+1相",
                "rgb": "ARGB",
            },
        ),
        (
            "mb-gigabyte-b760m-d4",
            "B760M AORUS ELITE AX DDR4",
            "技嘉 GIGABYTE",
            999,
            {
                "socket": "LGA1700",
                "chipset": "Intel B760",
                "memory_type": "DDR4",
                "form_factor": "mATX",
                "max_memory_gb": 128,
                "memory_slots": 4,
                "m2_slots": 2,
                "sata_ports": 4,
                "gpu_slot": "PCIe 4.0 x16",
                "wifi": "Wi-Fi 6E",
                "power_phase": "12+1+1相",
                "rgb": "RGB Fusion",
            },
        ),
        (
            "mb-asus-z890-e",
            "ROG STRIX Z890-E GAMING WIFI",
            "华硕 ASUS",
            3799,
            {
                "socket": "LGA1851",
                "chipset": "Intel Z890",
                "memory_type": "DDR5",
                "form_factor": "ATX",
                "max_memory_gb": 256,
                "memory_slots": 4,
                "m2_slots": 7,
                "sata_ports": 4,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 7",
                "power_phase": "18+1+2+2相",
                "rgb": "Aura Sync",
            },
        ),
        (
            "mb-msi-b860i-edge",
            "MPG B860I EDGE TI WIFI",
            "微星 MSI",
            2199,
            {
                "socket": "LGA1851",
                "chipset": "Intel B860",
                "memory_type": "DDR5",
                "form_factor": "Mini-ITX",
                "max_memory_gb": 128,
                "memory_slots": 2,
                "m2_slots": 3,
                "sata_ports": 2,
                "gpu_slot": "PCIe 5.0 x16",
                "wifi": "Wi-Fi 7",
                "power_phase": "8+1+1+1相",
                "rgb": "ARGB",
            },
        ),
    ]
    board_parts = [
        _part(
            item_id,
            PartCategory.MOTHERBOARD,
            name,
            brand,
            price,
            specs,
            summary="结构化主板参数用于插槽、内存代际、板型和扩展接口检查。",
        )
        for item_id, name, brand, price, specs in board_rows
    ]
    return cpu_parts + gpu_parts + aib_gpu_parts + board_parts


CPU_RANKING = [
    "cpu-9950x3d",
    "cpu-9950x",
    "cpu-9800x3d",
    "cpu-ultra9-285k",
    "cpu-14900k",
    "cpu-14700kf",
    "cpu-9700x",
    "cpu-ultra7-265k",
    "cpu-7800x3d",
    "cpu-14600kf",
    "cpu-9600x",
    "cpu-7700",
    "cpu-13600kf",
    "cpu-ultra5-245k",
    "cpu-12600kf",
    "cpu-13400f",
    "cpu-7600",
    "cpu-12100f",
]

GPU_RANKING = [
    "gpu-5090d",
    "gpu-5080",
    "gpu-4090",
    "gpu-5070ti",
    "gpu-4080s",
    "gpu-rx9070xt",
    "gpu-5070",
    "gpu-rx7900xtx",
    "gpu-4070tis",
    "gpu-rx9070",
    "gpu-4070s",
    "gpu-rx7900xt",
    "gpu-rx7800xt",
    "gpu-4070",
    "gpu-rx7700xt",
    "gpu-5060ti",
    "gpu-4060ti",
    "gpu-rx7600",
    "gpu-5060",
    "gpu-4060",
]


def apply_ladder_metadata(parts: list[Part]) -> None:
    for ranking, category, source_url in (
        (CPU_RANKING, PartCategory.CPU, CPU_LADDER_URL),
        (GPU_RANKING, PartCategory.GPU, GPU_LADDER_URL),
    ):
        count = len(ranking)
        for index, item_id in enumerate(ranking):
            part = next((candidate for candidate in parts if candidate.id == item_id), None)
            if part is None:
                continue
            score = max(52, 100 - round(index * 42 / max(1, count - 1)))
            part.rank = index + 1
            part.percentile = round(100 - index * 80 / max(1, count - 1), 2)
            part.benchmark_score = part.benchmark_score or score * 10000
            part.specs["score"] = score
            part.source = f"{part.source}；天梯结构参考：中关村在线"
            part.url = part.url or source_url
            part.data_updated_at = part.data_updated_at or "2026-08-30"
            if not part.summary:
                part.summary = "用于同类硬件横向比较，实际表现受整机与负载影响。"
            if not part.advantages:
                part.advantages = ["覆盖当前主流平台，可结合预算与目标分辨率筛选。"]
            if not part.cautions:
                part.cautions = ["排名为本地归一化参考，购买前需核对具体非公版型号参数。"]
            assert part.category == category
