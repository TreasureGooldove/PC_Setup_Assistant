from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

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


class FormFactorPreference(StrEnum):
    ANY = "any"
    ATX = "ATX"
    MATX = "mATX"
    ITX = "Mini-ITX"


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
    form_factor: FormFactorPreference = FormFactorPreference.ANY
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
    summary: str = ""
    rank: int | None = Field(default=None, ge=1)
    benchmark_score: int | None = Field(default=None, ge=0)
    percentile: float | None = Field(default=None, ge=0, le=100)
    advantages: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    data_updated_at: str | None = None


class Offer(BaseModel):
    part_id: str
    # 未配置授权报价或平台未返回可核验金额时保留为空，禁止用目录价推导平台价。
    price: float | None = Field(default=None, ge=0)
    source: str
    captured_at: datetime | None = None
    platform: str = "fixture"
    sku: str | None = None
    list_price: float | None = Field(default=None, ge=0)
    discount_price: float | None = Field(default=None, ge=0)
    landed_price: float | None = Field(default=None, ge=0)
    seller: str | None = None
    region: str | None = None
    coupon_note: str | None = None
    status: str = "参考价"
    url: str | None = None
    is_live: bool = False


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


class CommunityEvidence(BaseModel):
    """社区检索摘要；只保留可展示、可追溯的短字段。"""

    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=400)
    url: str
    author: str | None = Field(default=None, max_length=100)
    published_at: str | None = Field(default=None, max_length=60)
    source: str = "百度贴吧"
    confidence: Literal["low"] = "low"
    status: Literal["live", "reference"] = "live"


class CommunitySearchResult(BaseModel):
    """社区来源的可审计状态，不携带 MCP 原始响应。"""

    query: str = Field(min_length=1, max_length=180)
    status: Literal["disabled", "live", "empty", "unavailable"]
    provider: str
    note: str = Field(max_length=300)
    search_url: str | None = None
    items: list[CommunityEvidence] = Field(default_factory=list, max_length=8)


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
    source_kind: Literal["steam", "official", "fixture", "external"] = "steam"
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
    source_url: str | None = None
    data_updated_at: str | None = None
    note: str = ""


class DataSourceStatus(BaseModel):
    provider: str
    kind: str
    status: str
    note: str
    url: str | None = None
    captured_at: datetime | None = None


class ProductDetail(BaseModel):
    part: Part
    offers: list[Offer]
    evidence: list[Evidence] = Field(default_factory=list)
    sources: list[DataSourceStatus] = Field(default_factory=list)


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


class AgentStage(BaseModel):
    """展示给用户的阶段摘要，不是模型隐藏推理或原始工具日志。"""

    id: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)
    status: Literal["pending", "running", "completed", "waiting", "failed"]
    summary: str = Field(min_length=1, max_length=300)
    sources: list[str] = Field(default_factory=list, max_length=8)


class AgentTrace(BaseModel):
    """可复现的 Agent 工作摘要与最终结果入口。"""

    stages: list[AgentStage] = Field(min_length=1, max_length=8)
    result_summary: str = Field(min_length=1, max_length=600)
    provider: str = Field(min_length=1, max_length=80)
    mode: Literal["offline", "live", "fallback"] = "offline"
    generated_at: datetime


def _default_agent_trace() -> AgentTrace:
    """兼容升级前已保存的建议记录。"""

    return AgentTrace(
        stages=[
            AgentStage(
                id="result",
                label="生成结论",
                status="completed",
                summary="历史建议未保存阶段摘要，当前仅展示已保存的结构化结果。",
                sources=["历史建议记录"],
            )
        ],
        result_summary="历史建议记录未保存过程摘要，请以当前配置和依据为准。",
        provider="历史记录",
        mode="offline",
        generated_at=datetime.now(UTC),
    )


class RecommendationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot: PartCategory
    part_id: str = Field(min_length=1, max_length=100)
    part_name: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=400)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)


class RecommendationCompatibilitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "warning", "error"]
    passed_checks: int = Field(ge=0, le=20)
    warnings: list[str] = Field(default_factory=list, max_length=12)
    errors: list[str] = Field(default_factory=list, max_length=12)


class RecommendationPriceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: int = Field(ge=2500, le=100000)
    total_price: float = Field(ge=0)
    difference: float
    status: Literal["within_budget", "over_budget", "reference_only"]
    source_notes: list[str] = Field(default_factory=list, max_length=12)


class RecommendationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    kind: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=400)
    url: str | None = None
    confidence: Literal["high", "medium", "low"] = "low"


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    plan_id: str
    plan_fingerprint: str = Field(min_length=32, max_length=64)
    headline: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=600)
    profile_summary: str = Field(min_length=1, max_length=500)
    decisions: list[RecommendationDecision] = Field(min_length=1, max_length=12)
    compatibility_summary: RecommendationCompatibilitySummary
    price_summary: RecommendationPriceSummary
    evidence: list[RecommendationEvidence] = Field(default_factory=list, max_length=24)
    uncertainties: list[str] = Field(default_factory=list, max_length=12)
    next_actions: list[str] = Field(default_factory=list, max_length=12)
    agent_trace: AgentTrace = Field(default_factory=_default_agent_trace)
    provider: str = Field(min_length=1, max_length=40)
    source_status: str = Field(min_length=1, max_length=80)
    generated_at: datetime
    stale: bool = False


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_app_id: str | None = Field(
        default=None,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,79}$",
    )
    community_query: str | None = Field(default=None, min_length=1, max_length=180)
    include_community_evidence: bool = True


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
