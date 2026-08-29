from __future__ import annotations

from math import ceil

from app.domain import BuildItem, CompatibilityIssue, PartCategory


def check_compatibility(items: list[BuildItem]) -> list[CompatibilityIssue]:
    by_slot = {item.slot: item.part for item in items}
    issues: list[CompatibilityIssue] = []
    cpu = by_slot.get(PartCategory.CPU)
    board = by_slot.get(PartCategory.MOTHERBOARD)
    gpu = by_slot.get(PartCategory.GPU)
    memory = by_slot.get(PartCategory.MEMORY)
    psu = by_slot.get(PartCategory.PSU)
    cooler = by_slot.get(PartCategory.COOLING)
    case = by_slot.get(PartCategory.CASE)

    if cpu and board and cpu.specs.get("socket") != board.specs.get("socket"):
        issues.append(
            CompatibilityIssue(
                code="CPU_SOCKET",
                severity="error",
                title="CPU 与主板插槽不匹配",
                detail="两者的插槽规格不同，无法正常安装。",
                related_slots=["cpu", "motherboard"],
            )
        )
    if board and memory and board.specs.get("memory_type") != memory.specs.get("memory_type"):
        issues.append(
            CompatibilityIssue(
                code="MEMORY_TYPE",
                severity="error",
                title="内存代际不匹配",
                detail="主板与内存的 DDR 代际不同。",
                related_slots=["motherboard", "memory"],
            )
        )
    if gpu and case and gpu.specs.get("length_mm", 0) > case.specs.get("gpu_length_mm", 0):
        issues.append(
            CompatibilityIssue(
                code="GPU_LENGTH",
                severity="error",
                title="显卡长度超出机箱空间",
                detail="建议更换更大机箱或更短显卡。",
                related_slots=["gpu", "case"],
            )
        )
    if cooler and case:
        if cooler.specs.get("type") == "air" and cooler.specs.get("height_mm", 0) > case.specs.get(
            "cooler_height_mm", 0
        ):
            issues.append(
                CompatibilityIssue(
                    code="COOLER_HEIGHT",
                    severity="error",
                    title="风冷高度超出机箱限制",
                    detail="散热器高度超过机箱支持高度。",
                    related_slots=["cooling", "case"],
                )
            )
        if cooler.specs.get("type") == "water" and cooler.specs.get(
            "radiator_mm", 0
        ) > case.specs.get("radiator_mm", 0):
            issues.append(
                CompatibilityIssue(
                    code="RADIATOR_SIZE",
                    severity="error",
                    title="冷排尺寸超出机箱支持范围",
                    detail="请更换支持更大冷排的机箱。",
                    related_slots=["cooling", "case"],
                )
            )
    if cpu and cooler and cooler.specs.get("capacity_w", 0) < cpu.specs.get("tdp", 0) * 1.2:
        issues.append(
            CompatibilityIssue(
                code="COOLING_CAPACITY",
                severity="warning",
                title="散热余量偏小",
                detail="建议选择更高规格的散热器以获得更好的噪声与温度表现。",
                related_slots=["cpu", "cooling"],
            )
        )
    if psu:
        component_power = sum(part.power_w for part in by_slot.values()) + 80
        safe_required = ceil(component_power / 0.8)
        wattage = int(psu.specs.get("wattage", 0))
        if wattage < safe_required:
            issues.append(
                CompatibilityIssue(
                    code="PSU_HEADROOM",
                    severity="error",
                    title="电源余量不足",
                    detail=f"按建议余量至少需要 {safe_required}W，当前为 {wattage}W。",
                    related_slots=["psu"],
                )
            )
        elif wattage < safe_required + 100:
            issues.append(
                CompatibilityIssue(
                    code="PSU_MARGIN",
                    severity="warning",
                    title="电源升级余量有限",
                    detail="当前可用，但后续升级显卡时建议预留更高功率。",
                    related_slots=["psu"],
                )
            )
    return issues
