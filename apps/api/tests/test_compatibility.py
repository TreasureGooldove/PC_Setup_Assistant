from app.domain import BuildItem, Part, PartCategory
from app.features.builds.compatibility import check_compatibility


def make_part(item_id: str, category: PartCategory, specs: dict, power: int = 0) -> Part:
    return Part(
        id=item_id,
        category=category,
        name=item_id,
        brand="test",
        price=1,
        specs=specs,
        power_w=power,
    )


def test_detects_socket_memory_and_space_errors():
    items = [
        BuildItem(
            slot=PartCategory.CPU,
            part=make_part("cpu", PartCategory.CPU, {"socket": "AM5", "tdp": 65}, 65),
        ),
        BuildItem(
            slot=PartCategory.MOTHERBOARD,
            part=make_part(
                "board",
                PartCategory.MOTHERBOARD,
                {"socket": "LGA1700", "memory_type": "DDR4", "form_factor": "mATX"},
            ),
        ),
        BuildItem(
            slot=PartCategory.MEMORY,
            part=make_part("ram", PartCategory.MEMORY, {"memory_type": "DDR5"}),
        ),
        BuildItem(
            slot=PartCategory.GPU, part=make_part("gpu", PartCategory.GPU, {"length_mm": 400}, 300)
        ),
        BuildItem(slot=PartCategory.PSU, part=make_part("psu", PartCategory.PSU, {"wattage": 500})),
        BuildItem(
            slot=PartCategory.COOLING,
            part=make_part(
                "cooler", PartCategory.COOLING, {"type": "air", "height_mm": 180, "capacity_w": 80}
            ),
        ),
        BuildItem(
            slot=PartCategory.CASE,
            part=make_part(
                "case",
                PartCategory.CASE,
                {"gpu_length_mm": 300, "cooler_height_mm": 160, "radiator_mm": 240},
            ),
        ),
    ]
    codes = {issue.code for issue in check_compatibility(items)}
    assert {"CPU_SOCKET", "MEMORY_TYPE", "GPU_LENGTH", "COOLER_HEIGHT", "PSU_HEADROOM"}.issubset(
        codes
    )


def test_fixture_plan_is_compatible_for_defaults():
    from app.domain import NeedProfile
    from app.features.builds.planner import generate_plans

    plans = generate_plans(NeedProfile(budget=8000))
    assert len(plans) == 3
    assert all(issue.severity != "error" for plan in plans for issue in plan.compatibility)


def test_form_factor_preference_selects_itx_board_and_case():
    from app.domain import NeedProfile
    from app.features.builds.planner import generate_plans

    plans = generate_plans(NeedProfile(budget=12000, form_factor="Mini-ITX"))
    for plan in plans:
        board = next(item.part for item in plan.items if item.slot == PartCategory.MOTHERBOARD)
        case = next(item.part for item in plan.items if item.slot == PartCategory.CASE)
        assert board.specs["form_factor"] == "Mini-ITX"
        assert "Mini-ITX" in case.specs["supported_form_factors"]
        assert not any(issue.code == "FORM_FACTOR" for issue in plan.compatibility)


def test_detects_gpu_power_connector_shortage():
    items = [
        BuildItem(
            slot=PartCategory.GPU,
            part=make_part("gpu", PartCategory.GPU, {"power_connectors": ["2x8pin"]}, 200),
        ),
        BuildItem(
            slot=PartCategory.PSU,
            part=make_part("psu", PartCategory.PSU, {"wattage": 850, "pcie_8pin_count": 1}),
        ),
    ]
    assert any(issue.code == "GPU_POWER_CONNECTOR" for issue in check_compatibility(items))
