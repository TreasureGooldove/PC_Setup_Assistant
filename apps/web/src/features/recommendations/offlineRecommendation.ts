import type {
  AgentTrace,
  BuildPlan,
  GameRequirement,
  NeedProfile,
  Recommendation,
  RecommendationEvidence,
} from "../../types";

const SLOT_LABELS: Record<string, string> = {
  cpu: "处理器",
  motherboard: "主板",
  gpu: "显卡",
  memory: "内存",
  storage: "硬盘",
  psu: "电源",
  cooling: "散热",
  case: "机箱",
};

function profileLabels(profile: NeedProfile) {
  const cooling = profile.cooling === "air" ? "风冷" : profile.cooling === "water" ? "水冷" : "自动匹配散热";
  const formFactor = profile.form_factor === "any" ? "自动匹配机身" : profile.form_factor;
  return `${profile.use_case} · ${profile.resolution}/${profile.refresh_rate}Hz · ${cooling} · ${formFactor}`;
}

export function createOfflineRecommendation(
  plan: BuildPlan,
  profile: NeedProfile,
  game: GameRequirement | null,
): Recommendation {
  const errors = plan.compatibility.filter((item) => item.severity === "error").map((item) => item.detail);
  const warnings = plan.compatibility.filter((item) => item.severity !== "error").map((item) => item.detail);
  const sourceNotes = Array.from(new Set(plan.items.map((item) => `${item.part.name}：${item.part.source}`))).slice(0, 12);
  sourceNotes.unshift("当前金额为目录/公开参考价，未取得可核验实时成交价");
  const evidence: RecommendationEvidence[] = [
    {
      id: "need-profile",
      kind: "profile",
      label: "需求输入",
      source: "用户输入",
      summary: `预算 ${profile.budget.toLocaleString("zh-CN")} 元，用途为 ${profile.use_case}，目标 ${profile.resolution}/${profile.refresh_rate}Hz。`,
      confidence: "high" as const,
    },
    ...plan.items.map((item) => ({
      id: `part:${item.slot}`,
      kind: "part",
      label: item.part.name,
      source: item.part.source,
      summary: `${item.part.brand} ${item.part.name}，目录参考价 ${item.part.price.toLocaleString("zh-CN")} 元。`,
      url: item.part.url,
      confidence: "medium" as const,
    })),
    {
      id: "compatibility",
      kind: "compatibility",
      label: "兼容性复核",
      source: "本地确定性规则",
      summary: errors.length || warnings.length ? `发现 ${errors.length + warnings.length} 项需要关注的提示。` : "10 项装机规则均通过。",
      confidence: "high" as const,
    },
    {
      id: "price",
      kind: "price",
      label: "价格依据",
      source: "目录与公开参考价",
      summary: `整机参考价 ${plan.total_price.toLocaleString("zh-CN")} 元，当前未取得可核验实时成交价。`,
      confidence: "low" as const,
    },
  ];
  if (game) {
    evidence.push({
      id: "game-requirements",
      kind: "game",
      label: `${game.name} 配置要求`,
      source: game.source,
      summary: `已载入最低配置与推荐配置；最低显卡 ${game.minimum.graphics}，推荐显卡 ${game.recommended.graphics}。`,
      confidence: "medium" as const,
    });
  }

  const agentTrace: AgentTrace = {
    stages: [
      {
        id: "need",
        label: "需求识别",
        status: "completed",
        summary: `预算 ${profile.budget.toLocaleString("zh-CN")} 元，${profile.use_case}，目标 ${profile.resolution}/${profile.refresh_rate}Hz。`,
        sources: ["用户输入"],
      },
      {
        id: "research",
        label: "游戏与资料",
        status: game ? "completed" : "waiting",
        summary: game
          ? `已载入 ${game.name} 的配置资料；社区摘要未在离线演示中调用。`
          : "未指定游戏配置，保留通用装机判断。",
        sources: game ? [game.source] : ["未启用外部资料"],
      },
      {
        id: "candidates",
        label: "候选与价格",
        status: "completed",
        summary: `整理 ${plan.items.length} 个配置项，当前金额为目录/公开参考价。`,
        sources: ["本地候选目录", "价格状态"],
      },
      {
        id: "compatibility",
        label: "兼容性复核",
        status: "completed",
        summary: errors.length || warnings.length
          ? `发现 ${errors.length + warnings.length} 项需要关注的提示。`
          : "未发现硬性冲突。",
        sources: ["本地确定性兼容性规则"],
      },
      {
        id: "result",
        label: "生成结论",
        status: "completed",
        summary: "本地结构化建议已生成，金额与兼容性以当前方案为准。",
        sources: ["本地演示建议"],
      },
    ],
    result_summary: `预算约 ${profile.budget.toLocaleString("zh-CN")} 元，当前方案以 ${profile.resolution}/${profile.refresh_rate}Hz 为目标，以下是可核对的配置建议。`,
    provider: "mock",
    mode: "offline",
    generated_at: new Date().toISOString(),
  };

  return {
    id: `offline-${plan.id}`,
    plan_id: plan.id,
    plan_fingerprint: `offline-${plan.id}`.padEnd(64, "0").slice(0, 64),
    headline: `这套配置适合你的${profile.use_case}${game ? `，已参考 ${game.name}` : ""}`,
    summary: `预算约 ${profile.budget.toLocaleString("zh-CN")} 元，当前方案以 ${profile.resolution}/${profile.refresh_rate}Hz 为目标，以下是可核对的配置建议。`,
    profile_summary: profileLabels(profile),
    decisions: plan.items.map((item) => ({
      slot: item.slot,
      part_id: item.part.id,
      part_name: item.part.name,
      reason: item.reason || `按预算与兼容性选择${SLOT_LABELS[item.slot] ?? "配置项"}。`,
      evidence_ids: [`part:${item.slot}`, "compatibility", "price"],
    })),
    compatibility_summary: {
      status: errors.length ? "error" : warnings.length ? "warning" : "ok",
      passed_checks: Math.max(0, 10 - errors.length - warnings.length),
      warnings,
      errors,
    },
    price_summary: {
      budget: profile.budget,
      total_price: plan.total_price,
      difference: Math.round((plan.total_price - profile.budget) * 100) / 100,
      status: "reference_only",
      source_notes: sourceNotes,
    },
    evidence,
    uncertainties: [
      "当前金额是目录或公开参考价，购买前请核对具体店铺、规格和优惠。",
      ...(warnings.length ? ["兼容性检查中存在需要关注的提示，请按检查项逐一确认。"] : []),
    ],
    next_actions: ["优先核对显卡、主板和电源的具体商品规格。", "确认显示器接口与目标分辨率。"],
    agent_trace: agentTrace,
    provider: "mock",
    source_status: "本地演示建议（未启用外部模型）",
    generated_at: new Date().toISOString(),
    stale: false,
  };
}
