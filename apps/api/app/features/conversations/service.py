from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.database import ConversationRecord, SessionLocal, json_dump, json_load
from app.domain import ConversationResponse, NeedProfile
from app.errors import NotFoundError


def _parse_budget(text: str, fallback: int) -> int:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w|W|元|块)?", text)
    if not match:
        return fallback
    value = float(match.group(1))
    if match.group(2) in {"万", "w", "W"}:
        value *= 10000
    return max(2500, min(100000, int(value)))


def interpret_message(content: str, current: NeedProfile) -> NeedProfile:
    data = current.model_dump()
    data["budget"] = _parse_budget(content, current.budget)
    lowered = content.lower()
    if any(word in content for word in ["水冷", "冷排"]):
        data["cooling"] = "water"
    elif "风冷" in content:
        data["cooling"] = "air"
    if "英伟达" in content or "nvidia" in lowered or "n卡" in lowered or "显卡要n卡" in lowered:
        data["gpu_brand"] = "nvidia"
    elif "amd显卡" in lowered or "a卡" in lowered or "镭" in content:
        data["gpu_brand"] = "amd"
    if "amd处理器" in lowered or "amd cpu" in lowered or "锐龙" in content:
        data["cpu_brand"] = "amd"
    elif "intel" in lowered or "英特尔" in content:
        data["cpu_brand"] = "intel"
    for resolution in ["4K", "2K", "1080p", "1080P"]:
        if resolution in content:
            data["resolution"] = resolution.upper()
    if any(word in content for word in ["剪辑", "渲染", "生产力"]):
        data["use_case"] = "视频剪辑与生产力"
    elif any(word in content for word in ["游戏", "电竞", "网游", "战争雷霆"]):
        data["use_case"] = "游戏与日常"
    elif any(word in lowered for word in ["war thunder", "warthunder", "warthuder"]):
        data["use_case"] = "游戏与日常"
    if "静音" in content or "安静" in content:
        data["noise"] = "偏静音"
    if "白色" in content or "海景房" in content:
        data["aesthetics"] = "白色简洁"
    if re.search(r"(?:mini[- ]?itx|itx|迷你机|小钢炮)", lowered):
        data["form_factor"] = "Mini-ITX"
    elif re.search(r"(?:m[- ]?atx|matx|micro[- ]?atx|小机箱|紧凑)", lowered):
        data["form_factor"] = "mATX"
    elif re.search(r"(?:atx|标准机箱)", lowered):
        data["form_factor"] = "ATX"
    return NeedProfile.model_validate(data)


def create_conversation(profile: NeedProfile) -> ConversationResponse:
    conversation_id = str(uuid4())
    now = datetime.now(UTC)
    messages = [
        {
            "role": "assistant",
            "content": "你好，我会先了解你的用途和预算，再给出几套可解释的装机方案。",
            "created_at": now.isoformat(),
        }
    ]
    with SessionLocal() as session:
        session.add(
            ConversationRecord(
                id=conversation_id,
                profile_json=json_dump(profile.model_dump()),
                messages_json=json_dump(messages),
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    return ConversationResponse(id=conversation_id, profile=profile, messages=messages)


def get_conversation(conversation_id: str) -> ConversationResponse:
    with SessionLocal() as session:
        record = session.get(ConversationRecord, conversation_id)
        if not record:
            raise NotFoundError("对话", conversation_id)
        return ConversationResponse(
            id=record.id,
            profile=NeedProfile.model_validate(json_load(record.profile_json, {})),
            messages=json_load(record.messages_json, []),
        )


def append_message(conversation_id: str, content: str) -> ConversationResponse:
    now = datetime.now(UTC)
    with SessionLocal() as session:
        record = session.get(ConversationRecord, conversation_id)
        if not record:
            raise NotFoundError("对话", conversation_id)
        profile = interpret_message(
            content, NeedProfile.model_validate(json_load(record.profile_json, {}))
        )
        messages = json_load(record.messages_json, [])
        messages.extend(
            [
                {"role": "user", "content": content, "created_at": now.isoformat()},
                {"role": "assistant", "content": _reply(profile), "created_at": now.isoformat()},
            ]
        )
        record.profile_json = json_dump(profile.model_dump())
        record.messages_json = json_dump(messages)
        record.updated_at = now
        session.commit()
        return ConversationResponse(id=record.id, profile=profile, messages=messages)


def update_profile(conversation_id: str, profile: NeedProfile) -> ConversationResponse:
    with SessionLocal() as session:
        record = session.get(ConversationRecord, conversation_id)
        if not record:
            raise NotFoundError("对话", conversation_id)
        record.profile_json = json_dump(profile.model_dump())
        record.updated_at = datetime.now(UTC)
        session.commit()
    return get_conversation(conversation_id)


def _reply(profile: NeedProfile) -> str:
    return (
        f"收到：预算约 {profile.budget:,} 元，主要用于 {profile.use_case}，"
        f"目标 {profile.resolution}。正在整理可核对方案，完成后会进入方案工作台。"
    )
