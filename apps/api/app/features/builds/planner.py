from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain import (
    BuildItem,
    BuildPlan,
    NeedProfile,
    Part,
    PartCategory,
    PlanStyle,
)
from app.features.builds.catalog import fixture_parts
from app.features.builds.compatibility import check_compatibility


def _by_id(parts: list[Part], item_id: str) -> Part:
    return next(item for item in parts if item.id == item_id)


def _choose_gpu(parts: list[Part], profile: NeedProfile, style: PlanStyle) -> Part:
    brand = str(profile.gpu_brand)
    candidates = [
        p
        for p in parts
        if p.category == PartCategory.GPU and (brand == "any" or p.brand.lower() == brand)
    ]
    if not candidates:
        candidates = [p for p in parts if p.category == PartCategory.GPU]
    score_floor = {PlanStyle.VALUE: 70, PlanStyle.BALANCED: 82, PlanStyle.PERFORMANCE: 90}[style]
    eligible = [p for p in candidates if p.specs.get("score", 0) >= score_floor]
    return max(eligible or candidates, key=lambda p: p.specs.get("score", 0))


def _choose_cpu(parts: list[Part], profile: NeedProfile, style: PlanStyle) -> Part:
    brand = str(profile.cpu_brand)
    candidates = [
        p
        for p in parts
        if p.category == PartCategory.CPU and (brand == "any" or p.brand.lower() == brand)
    ]
    if not candidates:
        candidates = [p for p in parts if p.category == PartCategory.CPU]
    score_floor = {PlanStyle.VALUE: 75, PlanStyle.BALANCED: 84, PlanStyle.PERFORMANCE: 94}[style]
    eligible = [p for p in candidates if p.specs.get("score", 0) >= score_floor]
    return max(eligible or candidates, key=lambda p: p.specs.get("score", 0))


def _choose_parts(profile: NeedProfile, style: PlanStyle) -> list[Part]:
    parts = fixture_parts()
    cpu = _choose_cpu(parts, profile, style)
    gpu = _choose_gpu(parts, profile, style)
    if cpu.specs["socket"] == "AM5":
        board_id = "mb-b650" if style == PlanStyle.PERFORMANCE else "mb-b650m"
    else:
        board_id = "mb-z790" if style != PlanStyle.VALUE else "mb-b760m-ddr4"
    board = _by_id(parts, board_id)
    memory = _by_id(
        parts,
        "ram-ddr4-32"
        if board.specs["memory_type"] == "DDR4"
        else ("ram-ddr5-64" if style == PlanStyle.PERFORMANCE else "ram-ddr5-32"),
    )
    storage = _by_id(parts, "ssd-2tb-a" if style != PlanStyle.VALUE else "ssd-1tb-a")
    required_power = cpu.power_w + gpu.power_w + 80
    psu_id = (
        "psu-850" if required_power > 500 else ("psu-750" if required_power > 380 else "psu-650")
    )
    psu = _by_id(parts, psu_id)
    cooling_pref = str(profile.cooling)
    if cooling_pref == "water" or (cooling_pref == "any" and style == PlanStyle.PERFORMANCE):
        cooler = _by_id(parts, "cooler-water-240")
    else:
        cooler = _by_id(parts, "cooler-air-pro" if style == PlanStyle.PERFORMANCE else "cooler-air")
    case = _by_id(parts, "case-atx" if board.specs["form_factor"] == "ATX" else "case-matx")
    return [cpu, board, gpu, memory, storage, psu, cooler, case]


def generate_plans(profile: NeedProfile) -> list[BuildPlan]:
    labels = {
        PlanStyle.VALUE: ("省心省预算", "优先把预算留给实际体验，适合主流游戏与日常使用。"),
        PlanStyle.BALANCED: ("均衡耐用", "在性能、噪声和升级空间之间保持平衡。"),
        PlanStyle.PERFORMANCE: ("高性能释放", "优先保障高刷新率和更长的使用周期。"),
    }
    plans: list[BuildPlan] = []
    for style in (PlanStyle.VALUE, PlanStyle.BALANCED, PlanStyle.PERFORMANCE):
        selected = _choose_parts(profile, style)
        reasons = {
            PartCategory.CPU: (
                f"匹配 {profile.use_case}，CPU 综合参考分 {selected[0].specs.get('score')}。"
            ),
            PartCategory.GPU: (
                f"面向 {profile.resolution}/{profile.refresh_rate}，"
                f"显卡参考分 {selected[2].specs.get('score')}。"
            ),
            PartCategory.COOLING: "根据散热偏好与 CPU 热设计功耗选择。",
        }
        items = [
            BuildItem(
                slot=part.category,
                part=part,
                reason=reasons.get(part.category, "根据预算与兼容性自动选择。"),
            )
            for part in selected
        ]
        issues = check_compatibility(items)
        total = round(sum(item.part.price for item in items), 2)
        power = sum(part.power_w for part in selected) + 80
        score = min(
            99,
            int(
                selected[0].specs.get("score", 0) * 0.35 + selected[2].specs.get("score", 0) * 0.65
            ),
        )
        now = datetime.now(UTC)
        title, summary = labels[style]
        plans.append(
            BuildPlan(
                id=str(uuid4()),
                style=style,
                title=title,
                summary=summary,
                budget=profile.budget,
                total_price=total,
                estimated_power_w=power,
                performance_score=score,
                items=items,
                compatibility=issues,
                evidence=[],
                created_at=now,
            )
        )
    return plans
