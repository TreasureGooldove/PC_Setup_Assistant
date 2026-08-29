from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BrandPreference(StrEnum):
    ANY = "any"
    AMD = "amd"
    INTEL = "intel"
    NVIDIA = "nvidia"


class CoolingPreference(StrEnum):
    ANY = "any"
    AIR = "air"
    WATER = "water"


class PlanStyle(StrEnum):
    VALUE = "value"
    BALANCED = "balanced"
    PERFORMANCE = "performance"


class PartCategory(StrEnum):
    CPU = "cpu"
    MOTHERBOARD = "motherboard"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"
    PSU = "psu"
    COOLING = "cooling"
    CASE = "case"


class LadderCategory(StrEnum):
    CPU = "cpu"
    GPU = "gpu"


class NeedProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    budget: int = Field(default=8000, ge=2500, le=100000)
    use_case: str = Field(default="游戏与日常", min_length=1, max_length=200)
    resolution: str = Field(default="2K", max_length=20)
    refresh_rate: int = Field(default=165, ge=30, le=540)
    cpu_brand: BrandPreference = BrandPreference.ANY
    gpu_brand: BrandPreference = BrandPreference.ANY
    cooling: CoolingPreference = CoolingPreference.ANY
    aesthetics: str = Field(default="简洁", max_length=100)
    noise: str = Field(default="均衡", max_length=100)
    upgrade: str = Field(default="保留升级空间", max_length=200)
    existing_parts: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("existing_parts")
    @classmethod
    def clean_existing_parts(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()][:12]


class Part(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    category: PartCategory
    name: str
    brand: str
    price: float = Field(ge=0)
    source: str = "本地参考数据"
    url: str | None = None
    image_url: str | None = None
    specs: dict[str, Any] = Field(default_factory=dict)
    power_w: int = Field(default=0, ge=0)


class Offer(BaseModel):
    part_id: str
    price: float
    source: str
    captured_at: datetime
    status: str = "参考价"
    url: str | None = None


class CompatibilityIssue(BaseModel):
    code: str
    severity: str
    title: str
    detail: str
    related_slots: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    source: str
    title: str
    url: str | None = None
    summary: str
    confidence: str = "low"


class SystemRequirement(BaseModel):
    operating_system: str = "未提供"
    processor: str = "未提供"
    memory_gb: int | None = Field(default=None, ge=0)
    graphics: str = "未提供"
    directx: str | None = None
    storage_gb: int | None = Field(default=None, ge=0)
    additional_notes: str | None = None


class GameSearchResult(BaseModel):
    app_id: str
    name: str
    source: str = "Fixture游戏数据"


class GameRequirement(BaseModel):
    app_id: str
    name: str
    source: str = "Fixture游戏数据"
    minimum: SystemRequirement
    recommended: SystemRequirement
    notes: str = ""


class HardwareLadderEntry(BaseModel):
    id: str
    category: LadderCategory
    tier: str
    rank: int = Field(ge=1)
    name: str
    brand: str
    score: int = Field(ge=0, le=100)
    vram_gb: int | None = Field(default=None, ge=0)
    power_w: int | None = Field(default=None, ge=0)
    reference_price: float | None = Field(default=None, ge=0)
    source: str = "Fixture性能参考"
    note: str = ""


class BuildItem(BaseModel):
    slot: PartCategory
    part: Part
    locked: bool = False
    reason: str = ""
    offers: list[Offer] = Field(default_factory=list)


class BuildPlan(BaseModel):
    id: str
    style: PlanStyle
    title: str
    summary: str
    budget: int
    total_price: float
    estimated_power_w: int
    performance_score: int
    items: list[BuildItem]
    compatibility: list[CompatibilityIssue] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    created_at: datetime


class ConversationCreate(BaseModel):
    profile: NeedProfile = Field(default_factory=NeedProfile)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ProfileUpdate(BaseModel):
    profile: NeedProfile


class ConversationResponse(BaseModel):
    id: str
    profile: NeedProfile
    messages: list[dict[str, Any]]


class Job(BaseModel):
    id: str
    kind: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str = ""
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
