from __future__ import annotations

from app.domain import HardwareLadderEntry, LadderCategory, PartCategory
from app.features.builds.catalog import fixture_parts
from app.features.builds.catalog_expansion import CPU_LADDER_URL, GPU_LADDER_URL


def ladder_entries(
    category: LadderCategory | None = None,
    query: str = "",
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[HardwareLadderEntry]:
    entries: list[HardwareLadderEntry] = []
    for part in fixture_parts():
        if part.category not in (PartCategory.CPU, PartCategory.GPU) or part.rank is None:
            continue
        score = int(part.specs.get("score", 0))
        source_url = CPU_LADDER_URL if part.category == PartCategory.CPU else GPU_LADDER_URL
        entries.append(
            HardwareLadderEntry(
                id=part.id,
                category=LadderCategory(str(part.category)),
                tier="S" if score >= 93 else "A" if score >= 82 else "B" if score >= 70 else "C",
                rank=part.rank,
                name=part.name.removesuffix(" 8G").removesuffix(" 12G").removesuffix(" 16G"),
                brand=part.brand,
                score=score,
                vram_gb=int(part.specs.get("vram_gb", 0)) or None,
                power_w=part.power_w,
                reference_price=part.price,
                source="中关村在线天梯结构参考 / 本地归一化",
                source_url=source_url,
                data_updated_at=part.data_updated_at,
                note=part.summary[:42],
            )
        )
    entries.sort(key=lambda entry: (entry.category.value, entry.rank))
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
        result = [entry for entry in result if (entry.reference_price or 0) >= min_price]
    if max_price is not None:
        result = [entry for entry in result if (entry.reference_price or 0) <= max_price]
    return result
