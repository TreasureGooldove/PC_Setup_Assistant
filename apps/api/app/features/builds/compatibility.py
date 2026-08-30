from __future__ import annotations

from math import ceil
from typing import Any

from app.domain import BuildItem, CompatibilityIssue, PartCategory


def _issue(
    code: str,
    severity: str,
    title: str,
    detail: str,
    slots: list[str],
) -> CompatibilityIssue:
    return CompatibilityIssue(
        code=code,
        severity=severity,
        title=title,
        detail=detail,
        related_slots=slots,
    )


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


def _required_8pin(connectors: list[str]) -> int:
    total = 0
    for connector in connectors:
        if not connector.endswith("8pin") or "x" not in connector:
            continue
        count = connector.split("x", 1)[0]
        if count.isdigit():
            total += int(count)
    return total


def check_compatibility(items: list[BuildItem]) -> list[CompatibilityIssue]:
    by_slot = {item.slot: item.part for item in items}
    issues: list[CompatibilityIssue] = []
    cpu = by_slot.get(PartCategory.CPU)
    board = by_slot.get(PartCategory.MOTHERBOARD)
    gpu = by_slot.get(PartCategory.GPU)
    memory = by_slot.get(PartCategory.MEMORY)
    storage = by_slot.get(PartCategory.STORAGE)
    psu = by_slot.get(PartCategory.PSU)
    cooler = by_slot.get(PartCategory.COOLING)
    case = by_slot.get(PartCategory.CASE)

    if cpu and board:
        cpu_socket = cpu.specs.get("socket")
        board_socket = board.specs.get("socket")
        if cpu_socket and board_socket and cpu_socket != board_socket:
            issues.append(
                _issue(
                    "CPU_SOCKET",
                    "error",
                    "CPU 与主板插槽不匹配",
                    "两者的插槽规格不同，无法正常安装。",
                    ["cpu", "motherboard"],
                )
            )
        elif not cpu_socket or not board_socket:
            issues.append(
                _issue(
                    "CPU_SOCKET_UNKNOWN",
                    "warning",
                    "CPU 与主板插槽待确认",
                    "缺少插槽字段，暂不判定是否可以安装。",
                    ["cpu", "motherboard"],
                )
            )

    if board and memory:
        board_memory = board.specs.get("memory_type")
        memory_type = memory.specs.get("memory_type")
        if board_memory and memory_type and board_memory != memory_type:
            issues.append(
                _issue(
                    "MEMORY_TYPE",
                    "error",
                    "内存代际不匹配",
                    "主板与内存的 DDR 代际不同。",
                    ["motherboard", "memory"],
                )
            )
        elif not board_memory or not memory_type:
            issues.append(
                _issue(
                    "MEMORY_TYPE_UNKNOWN",
                    "warning",
                    "内存代际待确认",
                    "缺少主板或内存代际字段，暂不判定是否兼容。",
                    ["motherboard", "memory"],
                )
            )
        max_memory = board.specs.get("max_memory_gb")
        capacity = memory.specs.get("capacity_gb")
        if max_memory and capacity and int(capacity) > int(max_memory):
            issues.append(
                _issue(
                    "MEMORY_CAPACITY",
                    "error",
                    "内存容量超过主板上限",
                    f"当前套装为 {capacity}GB，主板标注上限为 {max_memory}GB。",
                    ["motherboard", "memory"],
                )
            )

    if board and case:
        board_size = board.specs.get("form_factor")
        supported_sizes = case.specs.get("supported_form_factors")
        if board_size or supported_sizes:
            if not board_size or not isinstance(supported_sizes, list):
                issues.append(
                    _issue(
                        "FORM_FACTOR_UNKNOWN",
                        "warning",
                        "主板与机箱尺寸待确认",
                        "缺少主板尺寸或机箱支持尺寸列表，暂不判定是否可以安装。",
                        ["motherboard", "case"],
                    )
                )
            elif board_size not in supported_sizes:
                supported_sizes_text = ", ".join(str(size) for size in supported_sizes)
                issues.append(
                    _issue(
                        "FORM_FACTOR",
                        "error",
                        "主板规格与机箱不匹配",
                        f"当前主板为 {board_size}，机箱支持：{supported_sizes_text}。",
                        ["motherboard", "case"],
                    )
                )

    if gpu and case:
        gpu_length = gpu.specs.get("length_mm")
        case_limit = case.specs.get("gpu_length_mm")
        if gpu_length is not None and case_limit is not None:
            if gpu_length > case_limit:
                issues.append(
                    _issue(
                        "GPU_LENGTH",
                        "error",
                        "显卡长度超出机箱空间",
                        "建议更换更大机箱或更短显卡。",
                        ["gpu", "case"],
                    )
                )
        else:
            issues.append(
                _issue(
                    "GPU_LENGTH_UNKNOWN",
                    "warning",
                    "显卡长度待确认",
                    "缺少显卡长度或机箱限长字段，建议打开商品规格页确认。",
                    ["gpu", "case"],
                )
            )

    if cpu and cooler:
        supported_sockets = cooler.specs.get("supported_sockets")
        if supported_sockets is not None:
            socket = cpu.specs.get("socket")
            supported_sockets_list = _as_list(supported_sockets)
            if not socket or not supported_sockets_list:
                issues.append(
                    _issue(
                        "COOLER_SOCKET_UNKNOWN",
                        "warning",
                        "散热器扣具待确认",
                        "缺少 CPU 插槽或散热器支持插槽字段。",
                        ["cpu", "cooling"],
                    )
                )
            elif socket not in supported_sockets_list:
                issues.append(
                    _issue(
                        "COOLER_SOCKET",
                        "error",
                        "散热器扣具与 CPU 插槽不匹配",
                        f"当前散热器支持 {', '.join(supported_sockets_list)}，不包含 {socket}。",
                        ["cpu", "cooling"],
                    )
                )

    if cooler and case:
        cooling_type = cooler.specs.get("type")
        if cooling_type == "air":
            cooler_height = cooler.specs.get("height_mm")
            case_height = case.specs.get("cooler_height_mm")
            if cooler_height is not None and case_height is not None:
                if cooler_height > case_height:
                    issues.append(
                        _issue(
                            "COOLER_HEIGHT",
                            "error",
                            "风冷高度超出机箱限制",
                            "散热器高度超过机箱支持高度。",
                            ["cooling", "case"],
                        )
                    )
            else:
                issues.append(
                    _issue(
                        "COOLER_HEIGHT_UNKNOWN",
                        "warning",
                        "风冷高度待确认",
                        "缺少散热器高度或机箱限高字段。",
                        ["cooling", "case"],
                    )
                )
        if cooling_type == "water":
            radiator = cooler.specs.get("radiator_mm")
            case_radiator = case.specs.get("radiator_mm")
            if radiator is not None and case_radiator is not None:
                if radiator > case_radiator:
                    issues.append(
                        _issue(
                            "RADIATOR_SIZE",
                            "error",
                            "冷排尺寸超出机箱支持范围",
                            "请更换支持更大冷排的机箱。",
                            ["cooling", "case"],
                        )
                    )
            else:
                issues.append(
                    _issue(
                        "RADIATOR_SIZE_UNKNOWN",
                        "warning",
                        "冷排尺寸待确认",
                        "缺少冷排尺寸或机箱冷排支持字段。",
                        ["cooling", "case"],
                    )
                )

    if cpu and cooler:
        capacity = cooler.specs.get("capacity_w")
        tdp = cpu.specs.get("tdp")
        if capacity is not None and tdp is not None:
            if capacity < tdp * 1.2:
                issues.append(
                    _issue(
                        "COOLING_CAPACITY",
                        "warning",
                        "散热余量偏小",
                        "建议选择更高规格的散热器以获得更好的噪声与温度表现。",
                        ["cpu", "cooling"],
                    )
                )
        else:
            issues.append(
                _issue(
                    "COOLING_CAPACITY_UNKNOWN",
                    "warning",
                    "散热能力待确认",
                    "缺少 CPU 功耗或散热器标称解热能力。",
                    ["cpu", "cooling"],
                )
            )

    if board and storage and storage.specs.get("connector"):
        connector = str(storage.specs["connector"]).upper()
        if connector == "M.2" and int(board.specs.get("m2_slots", 0)) < 1:
            issues.append(
                _issue(
                    "STORAGE_INTERFACE",
                    "error",
                    "主板没有可用的 M.2 插槽",
                    "当前硬盘使用 M.2 接口，请更换主板或硬盘。",
                    ["motherboard", "storage"],
                )
            )
        elif connector == "SATA" and int(board.specs.get("sata_ports", 0)) < 1:
            issues.append(
                _issue(
                    "STORAGE_INTERFACE",
                    "error",
                    "主板没有可用的 SATA 接口",
                    "当前硬盘使用 SATA 接口，请更换主板或硬盘。",
                    ["motherboard", "storage"],
                )
            )

    if gpu and psu and gpu.specs.get("power_connectors"):
        connectors = _as_list(gpu.specs["power_connectors"])
        if "12VHPWR" in connectors and not psu.specs.get("twelve_vhpwr", False):
            issues.append(
                _issue(
                    "GPU_POWER_CONNECTOR",
                    "error",
                    "电源缺少显卡供电接口",
                    "显卡需要 12VHPWR，当前电源未标注该接口。",
                    ["gpu", "psu"],
                )
            )
        required_8pin = _required_8pin(connectors)
        available_8pin = int(psu.specs.get("pcie_8pin_count", 0))
        if required_8pin > available_8pin:
            issues.append(
                _issue(
                    "GPU_POWER_CONNECTOR",
                    "error",
                    "电源 PCIe 供电线数量不足",
                    f"显卡需要 {required_8pin} 个 8pin 接口，当前电源标注 {available_8pin} 个。",
                    ["gpu", "psu"],
                )
            )

    if psu:
        wattage = psu.specs.get("wattage")
        if wattage is None:
            issues.append(
                _issue(
                    "PSU_HEADROOM_UNKNOWN",
                    "warning",
                    "电源功率余量待确认",
                    "缺少电源额定功率字段，无法计算余量。",
                    ["psu"],
                )
            )
        else:
            component_power = sum(part.power_w for part in by_slot.values()) + 80
            safe_required = ceil(component_power / 0.8)
            if int(wattage) < safe_required:
                issues.append(
                    _issue(
                        "PSU_HEADROOM",
                        "error",
                        "电源余量不足",
                        f"按建议余量至少需要 {safe_required}W，当前为 {wattage}W。",
                        ["psu"],
                    )
                )
            elif int(wattage) < safe_required + 100:
                issues.append(
                    _issue(
                        "PSU_MARGIN",
                        "warning",
                        "电源升级余量有限",
                        "当前可用，但后续升级显卡时建议预留更高功率。",
                        ["psu"],
                    )
                )
    return issues
