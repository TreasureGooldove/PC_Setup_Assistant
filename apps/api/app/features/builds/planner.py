from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain import (
    BuildItem,
    BuildPlan,
    CompatibilityIssue,
    FormFactorPreference,
    NeedProfile,
    Part,
    PartCategory,
    PlanStyle,
)
from app.features.builds.catalog import fixture_parts
from app.features.builds.compatibility import check_compatibility

LOW_BUDGET_CUTOFF = 6000


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
    if profile.budget < LOW_BUDGET_CUTOFF:
        return min(candidates, key=lambda part: part.price)
    if style != PlanStyle.PERFORMANCE:
        compact = [part for part in candidates if int(part.specs.get("length_mm", 999)) <= 330]
        candidates = compact or candidates
    target = {PlanStyle.VALUE: 72, PlanStyle.BALANCED: 84, PlanStyle.PERFORMANCE: 94}[style]
    return min(
        candidates,
        key=lambda part: (abs(int(part.specs.get("score", 0)) - target), part.price),
    )


def _choose_cpu(parts: list[Part], profile: NeedProfile, style: PlanStyle) -> Part:
    brand = str(profile.cpu_brand)
    candidates = [
        p
        for p in parts
        if p.category == PartCategory.CPU and (brand == "any" or p.brand.lower() == brand)
    ]
    if not candidates:
        candidates = [p for p in parts if p.category == PartCategory.CPU]
    if profile.budget < LOW_BUDGET_CUTOFF:
        return min(candidates, key=lambda part: part.price)
    target = {PlanStyle.VALUE: 76, PlanStyle.BALANCED: 86, PlanStyle.PERFORMANCE: 95}[style]
    return min(
        candidates,
        key=lambda part: (abs(int(part.specs.get("score", 0)) - target), part.price),
    )


def _choose_parts(profile: NeedProfile, style: PlanStyle) -> list[Part]:
    parts = fixture_parts()
    cpu = _choose_cpu(parts, profile, style)
    gpu = _choose_gpu(parts, profile, style)
    requested_form = str(profile.form_factor)
    if requested_form == FormFactorPreference.ITX:
        board_id = (
            "mb-itx-b650"
            if cpu.specs["socket"] == "AM5"
            else "mb-msi-b860i-edge"
            if cpu.specs["socket"] == "LGA1851"
            else "mb-itx-b760"
        )
    elif cpu.specs["socket"] == "AM5":
        board_id = "mb-b650" if style == PlanStyle.PERFORMANCE else "mb-b650m"
    elif cpu.specs["socket"] == "LGA1851":
        board_id = "mb-asus-z890-e"
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
    needs_12vhpwr = "12VHPWR" in gpu.specs.get("power_connectors", [])
    psu_id = (
        "psu-850"
        if required_power > 500 or needs_12vhpwr
        else ("psu-750" if required_power > 380 else "psu-650")
    )
    psu = _by_id(parts, psu_id)
    cooling_pref = str(profile.cooling)
    if cooling_pref == "water" or (cooling_pref == "any" and style == PlanStyle.PERFORMANCE):
        cooler = _by_id(parts, "cooler-water-240")
    else:
        cooler = _by_id(parts, "cooler-air-pro" if style == PlanStyle.PERFORMANCE else "cooler-air")
    case_ids = {"ATX": "case-atx", "mATX": "case-matx", "Mini-ITX": "case-itx"}
    case = _by_id(parts, case_ids.get(board.specs["form_factor"], "case-matx"))
    if profile.budget < LOW_BUDGET_CUTOFF:
        compatible_boards = [
            part
            for part in parts
            if part.category == PartCategory.MOTHERBOARD
            and part.specs.get("socket") == cpu.specs.get("socket")
            and (
                requested_form == FormFactorPreference.ANY
                or part.specs.get("form_factor") == requested_form
            )
        ]
        if compatible_boards:
            board = min(compatible_boards, key=lambda part: part.price)
        compatible_memory = [
            part
            for part in parts
            if part.category == PartCategory.MEMORY
            and part.specs.get("memory_type") == board.specs.get("memory_type")
        ]
        if compatible_memory:
            memory = min(compatible_memory, key=lambda part: part.price)
        compatible_storage = [part for part in parts if part.category == PartCategory.STORAGE]
        if compatible_storage:
            storage = min(compatible_storage, key=lambda part: part.price)
        compatible_cooling = [
            part
            for part in parts
            if part.category == PartCategory.COOLING
            and part.specs.get("type") == cooling_pref
            and cpu.specs.get("socket") in part.specs.get("supported_sockets", [])
        ]
        if cooling_pref == "any":
            compatible_cooling = [
                part
                for part in parts
                if part.category == PartCategory.COOLING
                and part.specs.get("type") == "air"
                and cpu.specs.get("socket") in part.specs.get("supported_sockets", [])
            ]
        if compatible_cooling:
            cooler = min(compatible_cooling, key=lambda part: part.price)
        compatible_cases = [
            part
            for part in parts
            if part.category == PartCategory.CASE
            and board.specs.get("form_factor") in part.specs.get("supported_form_factors", [])
        ]
        if compatible_cases:
            case = min(compatible_cases, key=lambda part: part.price)
    return [cpu, board, gpu, memory, storage, psu, cooler, case]


def generate_plans(profile: NeedProfile) -> list[BuildPlan]:
    labels = {
        PlanStyle.VALUE: ("省心省预算", "优先把预算留给实际体验，适合主流游戏与日常使用。"),
        PlanStyle.BALANCED: ("均衡耐用", "在性能、噪声和升级空间之间保持平衡。"),
        PlanStyle.PERFORMANCE: ("高性能释放", "优先保障高刷新率和更长的使用周期。"),
    }
    plans: list[BuildPlan] = []
    minimum_reference_total = round(
        sum(part.price for part in _choose_parts(profile, PlanStyle.VALUE)),
        2,
    )
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
        if total > profile.budget:
            if profile.budget < minimum_reference_total:
                budget_detail = (
                    f"当前数据中符合偏好的完整配置最低参考价约 {minimum_reference_total:.0f} 元，"
                    f"仍比预算高 {minimum_reference_total - profile.budget:.0f} 元；"
                    "可提高预算、暂不购买独立显卡，或改用已有配件。"
                )
            else:
                budget_detail = (
                    f"当前参考价约 {total:.0f} 元，超出预算 {total - profile.budget:.0f} 元，"
                    "可替换显卡、存储或散热器。"
                )
            issues.append(
                CompatibilityIssue(
                    code="BUDGET_OVER",
                    severity="warning",
                    title="方案高于当前预算",
                    detail=budget_detail,
                    related_slots=["gpu", "storage"],
                )
            )
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
