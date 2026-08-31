from __future__ import annotations

from datetime import UTC, datetime

from app.database import PlanRecord, SessionLocal, json_dump, json_load
from app.domain import BuildPlan, NeedProfile, PartCategory
from app.errors import NotFoundError
from app.features.builds.compatibility import check_compatibility
from app.features.builds.planner import generate_plans
from app.features.catalog_sync.service import find_catalog_part


def save_plans(conversation_id: str, profile: NeedProfile) -> list[BuildPlan]:
    plans = generate_plans(profile)
    with SessionLocal() as session:
        for plan in plans:
            session.add(
                PlanRecord(
                    id=plan.id,
                    conversation_id=conversation_id,
                    plan_json=json_dump(plan.model_dump()),
                )
            )
        session.commit()
    return plans


def get_plan(plan_id: str) -> BuildPlan:
    with SessionLocal() as session:
        record = session.get(PlanRecord, plan_id)
        if not record:
            raise NotFoundError("装机方案", plan_id)
        return BuildPlan.model_validate(json_load(record.plan_json, {}))


def list_plans(conversation_id: str) -> list[BuildPlan]:
    with SessionLocal() as session:
        records = (
            session.query(PlanRecord)
            .filter(PlanRecord.conversation_id == conversation_id)
            .order_by(PlanRecord.created_at)
            .all()
        )
        return [BuildPlan.model_validate(json_load(record.plan_json, {})) for record in records]


def replace_item(
    plan_id: str, slot: PartCategory, part_id: str, locked: bool | None = None
) -> BuildPlan:
    with SessionLocal() as session:
        record = session.get(PlanRecord, plan_id)
        if not record:
            raise NotFoundError("装机方案", plan_id)
        plan = BuildPlan.model_validate(json_load(record.plan_json, {}))
        part = find_catalog_part(part_id)
        if not part or part.category != slot:
            raise NotFoundError("配件", part_id)
        item = next((item for item in plan.items if item.slot == slot), None)
        if not item:
            raise NotFoundError("配置项", slot.value)
        item.part = part
        if locked is not None:
            item.locked = locked
        plan.total_price = round(sum(item.part.price for item in plan.items), 2)
        plan.estimated_power_w = sum(item.part.power_w for item in plan.items) + 80
        plan.compatibility = check_compatibility(plan.items)
        record.plan_json = json_dump(plan.model_dump())
        record.updated_at = datetime.now(UTC)
        session.commit()
        return plan


def mark_refreshed(plan_id: str) -> BuildPlan:
    """Fixture 刷新保留接口；真实 Provider 会在这里更新 offers。"""
    return get_plan(plan_id)
