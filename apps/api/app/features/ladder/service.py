from __future__ import annotations

from app.domain import HardwareLadderEntry, LadderCategory


def ladder_entries(
    category: LadderCategory | None = None,
    query: str = "",
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[HardwareLadderEntry]:
    entries = [
        HardwareLadderEntry(
            id="cpu-7800x3d",
            category=LadderCategory.CPU,
            tier="S",
            rank=1,
            name="Ryzen 7 7800X3D",
            brand="AMD",
            score=98,
            power_w=120,
            reference_price=2499,
            note="游戏性能参考",
        ),
        HardwareLadderEntry(
            id="cpu-14600kf",
            category=LadderCategory.CPU,
            tier="A",
            rank=2,
            name="Core i5-14600KF",
            brand="Intel",
            score=91,
            power_w=125,
            reference_price=1799,
            note="游戏与生产力均衡",
        ),
        HardwareLadderEntry(
            id="cpu-7700",
            category=LadderCategory.CPU,
            tier="A",
            rank=3,
            name="Ryzen 7 7700",
            brand="AMD",
            score=86,
            power_w=65,
            reference_price=1599,
            note="低功耗与升级空间",
        ),
        HardwareLadderEntry(
            id="cpu-12600kf",
            category=LadderCategory.CPU,
            tier="B",
            rank=4,
            name="Core i5-12600KF",
            brand="Intel",
            score=82,
            power_w=125,
            reference_price=999,
            note="DDR4/DDR5 平台灵活",
        ),
        HardwareLadderEntry(
            id="cpu-13400f",
            category=LadderCategory.CPU,
            tier="B",
            rank=5,
            name="Core i5-13400F",
            brand="Intel",
            score=78,
            power_w=65,
            reference_price=1099,
            note="主流预算方案",
        ),
        HardwareLadderEntry(
            id="gpu-4070s",
            category=LadderCategory.GPU,
            tier="S",
            rank=1,
            name="GeForce RTX 4070 SUPER",
            brand="NVIDIA",
            score=94,
            vram_gb=12,
            power_w=220,
            reference_price=4499,
            note="2K 高刷参考",
        ),
        HardwareLadderEntry(
            id="gpu-rx7800xt",
            category=LadderCategory.GPU,
            tier="A",
            rank=2,
            name="Radeon RX 7800 XT",
            brand="AMD",
            score=91,
            vram_gb=16,
            power_w=263,
            reference_price=3899,
            note="显存充足",
        ),
        HardwareLadderEntry(
            id="gpu-4060ti",
            category=LadderCategory.GPU,
            tier="B",
            rank=3,
            name="GeForce RTX 4060 Ti",
            brand="NVIDIA",
            score=78,
            vram_gb=8,
            power_w=160,
            reference_price=2499,
            note="能效与光追",
        ),
        HardwareLadderEntry(
            id="gpu-rx7600",
            category=LadderCategory.GPU,
            tier="B",
            rank=4,
            name="Radeon RX 7600",
            brand="AMD",
            score=74,
            vram_gb=8,
            power_w=165,
            reference_price=2099,
            note="1080P 性价比",
        ),
    ]
    result = entries
    if category is not None:
        result = [entry for entry in result if entry.category == category]
    needle = query.strip().lower()
    if needle:
        result = [
            entry
            for entry in result
            if needle in entry.name.lower() or needle in entry.note.lower()
        ]
    if brand:
        result = [entry for entry in result if entry.brand.lower() == brand.strip().lower()]
    if min_price is not None:
        result = [
            entry for entry in result if (entry.reference_price or 0) >= min_price
        ]
    if max_price is not None:
        result = [
            entry for entry in result if (entry.reference_price or 0) <= max_price
        ]
    return result
