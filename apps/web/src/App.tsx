import {
  AlertTriangle,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Cpu,
  Database,
  Download,
  Gauge,
  Gamepad2,
  Lock,
  MessageSquare,
  RefreshCw,
  Search,
  Send,
  Settings2,
  Sparkles,
  Thermometer,
  Trophy,
  Unlock,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, streamJob } from "./api";
import { PartPicker } from "./features/catalog/PartPicker";
import { OFFLINE_CATALOG } from "./features/catalog/offlineCatalog";
import { ProductDetailPage } from "./features/catalog/ProductDetailPage";
import { RecommendationCard } from "./features/recommendations/RecommendationCard";
import { createOfflineRecommendation } from "./features/recommendations/offlineRecommendation";
import { RequestInsightPanel } from "./features/recommendations/RequestInsightPanel";
import type {
  AppView,
  BuildItem,
  BuildPlan,
  CatalogSyncStatus,
  CompatibilityIssue,
  ConversationResponse,
  GameRequirement,
  GameSearchResult,
  HardwareLadderEntry,
  LadderCategory,
  NeedProfile,
  Offer,
  Part,
  PartCategory,
  ProductDetail,
  Recommendation,
  SystemRequirement,
} from "./types";

type Theme = "corporate" | "glass" | "neumorphism";

const DEFAULT_PROFILE: NeedProfile = {
  budget: 8000,
  use_case: "游戏与日常",
  resolution: "2K",
  refresh_rate: 165,
  cpu_brand: "any",
  gpu_brand: "any",
  cooling: "any",
  form_factor: "any",
  aesthetics: "简洁",
  noise: "均衡",
  upgrade: "保留升级空间",
  existing_parts: [],
};

const MIN_BUDGET = 2500;
const SLIDER_MAX_BUDGET = 20000;
const MAX_CUSTOM_BUDGET = 100000;

function normalizeBudget(value: number) {
  if (!Number.isFinite(value)) return MIN_BUDGET;
  return Math.min(
    MAX_CUSTOM_BUDGET,
    Math.max(MIN_BUDGET, Math.round(value)),
  );
}

function budgetValidationMessage(value: string) {
  if (!value.trim()) return "请输入预算";
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "请输入有效数字";
  if (amount < MIN_BUDGET) return `最低预算为 ¥${formatMoney(MIN_BUDGET)}`;
  if (amount > MAX_CUSTOM_BUDGET)
    return `最高预算为 ¥${formatMoney(MAX_CUSTOM_BUDGET)}`;
  return "支持精确到 1 元，生成前会自动校准";
}

const SLOT_LABELS: Record<PartCategory, string> = {
  cpu: "处理器",
  motherboard: "主板",
  gpu: "显卡",
  memory: "内存",
  storage: "硬盘",
  psu: "电源",
  cooling: "散热",
  case: "机箱",
};

const DEMO_PARTS: Record<string, Part> = {
  cpu: {
    id: "demo-cpu",
    category: "cpu",
    name: "Ryzen 7 7700",
    brand: "AMD",
    price: 1599,
    source: "Fixture参考价",
    specs: { socket: "AM5", tdp: 65 },
    power_w: 65,
  },
  motherboard: {
    id: "demo-board",
    category: "motherboard",
    name: "B650M WiFi 主板",
    brand: "AMD平台",
    price: 899,
    source: "Fixture参考价",
    specs: {
      socket: "AM5",
      memory_type: "DDR5",
      form_factor: "mATX",
      m2_slots: 2,
      sata_ports: 4,
      gpu_slot: "PCIe4 x16",
    },
    power_w: 0,
  },
  gpu: {
    id: "demo-gpu",
    category: "gpu",
    name: "GeForce RTX 4070 SUPER 12G",
    brand: "NVIDIA",
    price: 4499,
    source: "Fixture参考价",
    specs: {
      length_mm: 300,
      pcie_slot: "PCIe4 x16",
      power_connectors: ["12VHPWR"],
    },
    power_w: 220,
  },
  memory: {
    id: "demo-memory",
    category: "memory",
    name: "DDR5 6000 32GB套装",
    brand: "金百达",
    price: 699,
    source: "Fixture参考价",
    specs: { memory_type: "DDR5" },
    power_w: 0,
  },
  storage: {
    id: "demo-storage",
    category: "storage",
    name: "1TB PCIe 4.0 固态硬盘",
    brand: "西数",
    price: 499,
    source: "Fixture参考价",
    specs: { capacity_gb: 1024, interface: "PCIe4", connector: "M.2" },
    power_w: 0,
  },
  psu: {
    id: "demo-psu",
    category: "psu",
    name: "750W 金牌全模组电源",
    brand: "安钛克",
    price: 799,
    source: "Fixture参考价",
    specs: {
      wattage: 750,
      pcie_8pin_count: 3,
      atx_3_0: false,
      twelve_vhpwr: false,
    },
    power_w: 0,
  },
  cooling: {
    id: "demo-cooling",
    category: "cooling",
    name: "双塔风冷散热器",
    brand: "利民",
    price: 199,
    source: "Fixture参考价",
    specs: {
      type: "air",
      height_mm: 157,
      capacity_w: 220,
      supported_sockets: ["AM5", "LGA1700"],
    },
    power_w: 0,
  },
  case: {
    id: "demo-case",
    category: "case",
    name: "通风型 ATX 机箱",
    brand: "乔思伯",
    price: 499,
    source: "Fixture参考价",
    specs: {
      form_factor: "ATX",
      supported_form_factors: ["ATX", "mATX", "Mini-ITX"],
      gpu_length_mm: 360,
      cooler_height_mm: 170,
      radiator_mm: 360,
    },
    power_w: 0,
  },
};

const LOCAL_LADDER: HardwareLadderEntry[] = [
  {
    id: "cpu-7800x3d",
    category: "cpu",
    tier: "S",
    rank: 1,
    name: "Ryzen 7 7800X3D",
    brand: "AMD",
    score: 98,
    power_w: 120,
    reference_price: 2499,
    source: "Fixture性能参考",
    note: "游戏性能参考",
  },
  {
    id: "cpu-14600kf",
    category: "cpu",
    tier: "A",
    rank: 2,
    name: "Core i5-14600KF",
    brand: "Intel",
    score: 91,
    power_w: 125,
    reference_price: 1799,
    source: "Fixture性能参考",
    note: "游戏与生产力均衡",
  },
  {
    id: "cpu-7700",
    category: "cpu",
    tier: "A",
    rank: 3,
    name: "Ryzen 7 7700",
    brand: "AMD",
    score: 86,
    power_w: 65,
    reference_price: 1599,
    source: "Fixture性能参考",
    note: "低功耗与升级空间",
  },
  {
    id: "cpu-12600kf",
    category: "cpu",
    tier: "B",
    rank: 4,
    name: "Core i5-12600KF",
    brand: "Intel",
    score: 82,
    power_w: 125,
    reference_price: 1199,
    source: "太平洋电脑网规格页 / Fixture参考价",
    note: "10核16线程，支持 DDR4 / DDR5",
  },
  {
    id: "cpu-13400f",
    category: "cpu",
    tier: "B",
    rank: 5,
    name: "Core i5-13400F",
    brand: "Intel",
    score: 78,
    power_w: 65,
    reference_price: 1099,
    source: "Fixture性能参考",
    note: "主流预算方案",
  },
  {
    id: "gpu-4070s",
    category: "gpu",
    tier: "S",
    rank: 1,
    name: "GeForce RTX 4070 SUPER",
    brand: "NVIDIA",
    score: 94,
    vram_gb: 12,
    power_w: 220,
    reference_price: 4499,
    source: "Fixture性能参考",
    note: "2K 高刷参考",
  },
  {
    id: "gpu-rx7800xt",
    category: "gpu",
    tier: "A",
    rank: 2,
    name: "Radeon RX 7800 XT",
    brand: "AMD",
    score: 91,
    vram_gb: 16,
    power_w: 263,
    reference_price: 3899,
    source: "Fixture性能参考",
    note: "显存充足",
  },
  {
    id: "gpu-4060ti",
    category: "gpu",
    tier: "B",
    rank: 3,
    name: "GeForce RTX 4060 Ti",
    brand: "NVIDIA",
    score: 78,
    vram_gb: 8,
    power_w: 160,
    reference_price: 2499,
    source: "Fixture性能参考",
    note: "能效与光追",
  },
  {
    id: "gpu-rx7600",
    category: "gpu",
    tier: "B",
    rank: 4,
    name: "Radeon RX 7600",
    brand: "AMD",
    score: 74,
    vram_gb: 8,
    power_w: 165,
    reference_price: 2099,
    source: "Fixture性能参考",
    note: "1080P 性价比",
  },
];

const LOCAL_LADDER_ITEMS: HardwareLadderEntry[] = Array.from(
  new Map(
    [
      ...OFFLINE_CATALOG.filter(
        (part) => part.category === "cpu" || part.category === "gpu",
      ).map((part) => {
        const score = Number(part.specs.score ?? 0);
        return {
          id: part.id,
          category: part.category as LadderCategory,
          tier: score >= 93 ? "S" : score >= 82 ? "A" : score >= 70 ? "B" : "C",
          rank: part.rank ?? 99,
          name: part.name.replace(/ \d+G$/, ""),
          brand: part.brand,
          score,
          vram_gb: Number(part.specs.vram_gb ?? 0) || null,
          power_w: part.power_w,
          reference_price: part.price,
          source: "中关村在线天梯结构参考 / 本地归一化",
          source_url: part.url,
          data_updated_at: part.data_updated_at,
          note: part.summary ?? "性能层级参考",
        } satisfies HardwareLadderEntry;
      }),
      ...LOCAL_LADDER,
    ].map((entry) => [entry.id, entry]),
  ).values(),
).sort((left, right) => left.rank - right.rank);

const LOCAL_CATALOG: Part[] = [
  ...Object.values(DEMO_PARTS),
  ...OFFLINE_CATALOG,
  {
    id: "cpu-12600kf",
    category: "cpu",
    name: "Core i5-12600KF",
    brand: "Intel",
    price: 1199,
    source: "太平洋电脑网规格页 / Fixture参考价",
    url: "https://product.pconline.com.cn/cpu/intel/1447887.html",
    specs: {
      socket: "LGA1700",
      cores_threads: "10核16线程",
      base_clock: "3.7GHz",
      boost_clock: "4.9GHz",
      tdp: 125,
      integrated_graphics: false,
      l3_cache: "20MB",
      process: "Intel 7",
      architecture: "Alder Lake",
      memory_types: ["DDR4", "DDR5"],
      launch_year: 2021,
    },
    power_w: 125,
    summary: "Alder Lake 桌面处理器，适合中高端游戏与多任务装机。",
    rank: 4,
    benchmark_score: 646985,
    percentile: 81.16,
    advantages: ["单核性能较强，游戏表现均衡，兼容 DDR4 / DDR5 平台。"],
    cautions: ["不带核显，需要独立显卡；满载功耗较高，应搭配合适散热和主板。"],
    data_updated_at: "2026-08-30",
  },
  {
    ...DEMO_PARTS.gpu,
    id: "gpu-rx7600",
    name: "Radeon RX 7600 8G",
    brand: "AMD",
    price: 2099,
    power_w: 165,
    summary: "面向 1080P 游戏的主流显卡，适合预算型方案。",
    rank: 4,
    benchmark_score: 74,
    percentile: 68.5,
    advantages: ["1080P 游戏性能和价格较均衡。"],
    cautions: ["2K 高画质和光追场景需要适当降低设置。"],
  },
];

function localProductDetail(part: Part): ProductDetail {
  const keyword = encodeURIComponent(part.name);
  const offers: Offer[] = [
    {
      part_id: part.id,
      source: "京东平台搜索入口",
      platform: "jd",
      status: "待联网",
      is_live: false,
      url: `https://search.jd.com/Search?keyword=${keyword}`,
    },
    {
      part_id: part.id,
      source: "拼多多平台搜索入口",
      platform: "pdd",
      status: "待联网",
      is_live: false,
      url: `https://mobile.yangkeduo.com/search_result.html?search_key=${keyword}`,
    },
  ];
  const sourceTitle =
    part.category === "cpu"
      ? "ZOL CPU 天梯"
      : part.category === "gpu"
        ? "ZOL 显卡天梯"
        : "ZOL DIY 硬件频道";
  return {
    part,
    offers,
    evidence: [
      {
        source: "中关村在线",
        title: sourceTitle,
        url: part.url,
        summary: "用于性能层级、参数字段和资料入口参考；价格不作为实时成交价。",
        confidence: "medium",
      },
    ],
    sources: [
      {
        provider: "本地结构化目录",
        kind: "parameters",
        status: "reference",
        note: "离线可复现参数。",
      },
      {
        provider: "京东",
        kind: "price",
        status: "unavailable",
        note: "当前未连接授权报价接口，仅提供搜索入口，不显示推导金额。",
        url: offers[0].url,
      },
      {
        provider: "拼多多",
        kind: "price",
        status: "unavailable",
        note: "当前未连接授权报价接口，仅提供搜索入口，不显示推导金额。",
        url: offers[1].url,
      },
    ],
  };
}

function requirement(
  operating_system: string,
  processor: string,
  memory_gb: number,
  graphics: string,
  directx: string,
  storage_gb: number,
): SystemRequirement {
  return {
    operating_system,
    processor,
    memory_gb,
    graphics,
    directx,
    storage_gb,
  };
}

const LOCAL_GAMES: Record<string, GameRequirement> = {
  "730": {
    app_id: "730",
    name: "Counter-Strike 2",
    source: "Fixture游戏数据",
    minimum: requirement(
      "Windows 10",
      "Intel Core i5-750 或 AMD Ryzen 5 1600",
      8,
      "NVIDIA GTX 1060 / AMD RX 580",
      "DirectX 11",
      85,
    ),
    recommended: requirement(
      "Windows 10/11",
      "Intel Core i5-12400 或 AMD Ryzen 5 5600",
      16,
      "NVIDIA RTX 3060 / AMD RX 6600",
      "DirectX 11",
      85,
    ),
    notes: "推荐配置为本地参考整理，实际体验会随分辨率和画质设置变化。",
  },
  "1245620": {
    app_id: "1245620",
    name: "Elden Ring",
    source: "Fixture游戏数据",
    minimum: requirement(
      "Windows 10",
      "Intel Core i5-8400 或 AMD Ryzen 3 3300X",
      12,
      "NVIDIA GTX 1060 3GB / AMD RX 580 4GB",
      "DirectX 12",
      60,
    ),
    recommended: requirement(
      "Windows 10/11",
      "Intel Core i7-8700K 或 AMD Ryzen 5 3600X",
      16,
      "NVIDIA GTX 1070 8GB / AMD RX Vega 56 8GB",
      "DirectX 12",
      60,
    ),
    notes: "适合用 2K 目标做整机预算评估，建议为系统和更新预留额外空间。",
  },
  "236390": {
    app_id: "236390",
    name: "War Thunder",
    source: "Steam 商店系统需求快照",
    minimum: requirement(
      "Windows 10 64-bit",
      "双核 2.2 GHz",
      4,
      "AMD Radeon 77XX / NVIDIA GeForce GTX 660",
      "DirectX 11",
      70,
    ),
    recommended: requirement(
      "Windows 10/11 64-bit",
      "Intel Core i5 或 AMD Ryzen 5 3600 及以上",
      16,
      "NVIDIA GeForce GTX 1060 / AMD Radeon RX 570 及以上",
      "DirectX 12",
      95,
    ),
    notes:
      "来自 Steam 商店公开系统需求；联机体验还会受分辨率、画质与网络状况影响。",
  },
  "rsi:star-citizen": {
    app_id: "rsi:star-citizen",
    name: "Star Citizen（星际公民）",
    source: "RSI 官方 Game and Launcher Requirements",
    source_kind: "official",
    minimum: requirement(
      "Windows 10/11 64-bit",
      "支持 AVX/AVX2/FMA3 的四核处理器（Intel i7 Haswell+ 或 AMD Excavator+）",
      16,
      "支持 DirectX 11.1 且显存 4GB 以上",
      "DirectX 11.1",
      150,
    ),
    recommended: requirement(
      "Windows 10/11 64-bit",
      "官方未提供统一的推荐 CPU 型号",
      0,
      "官方未提供统一的推荐显卡型号",
      "未提供",
      150,
    ),
    notes:
      "RSI 官方页面主要提供最低要求；需要 SSD，Linux/macOS 不是官方支持平台。推荐档位请结合目标分辨率和实际版本测试。",
  },
};

const GAME_ALIASES: Record<string, string[]> = {
  "236390": ["warthuder", "warthunder", "war thunder", "战争雷霆"],
  "rsi:star-citizen": ["star citizen", "starcitizen", "星际公民", "sc"],
};

function normaliseSearchText(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]/g, "");
}

function matchesGameCandidate(query: string, needle: string, candidate: string) {
  const normalized = normaliseSearchText(candidate);
  if (normalized.length <= 2 && /^[a-z0-9]+$/i.test(normalized)) {
    return new RegExp(`(^|[^a-z0-9])${normalized}([^a-z0-9]|$)`, "i").test(query);
  }
  return normalized.includes(needle) || needle.includes(normalized);
}

function searchLocalGames(query: string) {
  const needle = normaliseSearchText(query);
  return Object.values(LOCAL_GAMES)
    .filter(
      (game) =>
        !needle ||
        game.app_id === query ||
        [game.name, ...(GAME_ALIASES[game.app_id] ?? [])].some((name) =>
          matchesGameCandidate(query, needle, name),
        ),
    )
    .map(({ app_id, name, source }) => ({ app_id, name, source }));
}

function findMentionedGame(content: string): GameRequirement | null {
  const needle = normaliseSearchText(content);
  if (!needle) return null;
  return (
    Object.values(LOCAL_GAMES).find((game) =>
      [game.name, ...(GAME_ALIASES[game.app_id] ?? [])].some((name) => {
        const candidate = normaliseSearchText(name);
        return candidate.length > 1 && matchesGameCandidate(content, needle, name);
      }),
    ) ?? null
  );
}

function demoPlans(profile: NeedProfile): BuildPlan[] {
  const now = new Date().toISOString();
  const styles: BuildPlan["style"][] = ["value", "balanced", "performance"];
  const titles = ["省心省预算", "均衡耐用", "高性能释放"];
  const summaries = [
    "优先把预算留给实际体验，适合主流游戏与日常使用。",
    "在性能、噪声和升级空间之间保持平衡。",
    "优先保障高刷新率和更长的使用周期。",
  ];
  const formFactor =
    profile.form_factor === "Mini-ITX"
      ? "Mini-ITX"
      : profile.form_factor === "ATX"
        ? "ATX"
        : "mATX";
  const board = {
    ...DEMO_PARTS.motherboard,
    id: `demo-board-${formFactor}`,
    name: `${formFactor} WiFi 主板`,
    specs: { ...DEMO_PARTS.motherboard.specs, form_factor: formFactor },
  };
  const casePart =
    formFactor === "Mini-ITX"
      ? {
          ...DEMO_PARTS.case,
          id: "demo-case-itx",
          name: "小钢炮 Mini-ITX 机箱",
          specs: {
            ...DEMO_PARTS.case.specs,
            form_factor: "Mini-ITX",
            supported_form_factors: ["Mini-ITX"],
            gpu_length_mm: 305,
            cooler_height_mm: 155,
            radiator_mm: 240,
          },
        }
      : formFactor === "ATX"
        ? DEMO_PARTS.case
        : {
            ...DEMO_PARTS.case,
            id: "demo-case-matx",
            name: "紧凑型 mATX 机箱",
            specs: {
              ...DEMO_PARTS.case.specs,
              form_factor: "mATX",
              supported_form_factors: ["mATX", "Mini-ITX"],
              gpu_length_mm: 330,
              cooler_height_mm: 165,
              radiator_mm: 240,
            },
        };
  const budgetConstrained = profile.budget < 6000;
  const findLowest = (
    category: PartCategory,
    predicate: (part: Part) => boolean = () => true,
  ) =>
    OFFLINE_CATALOG.filter(
      (part) => part.category === category && predicate(part),
    ).sort((left, right) => left.price - right.price)[0];
  const preferredCpu = budgetConstrained
    ? findLowest(
        "cpu",
        (part) =>
          profile.cpu_brand === "any" ||
          part.brand.toLowerCase() === profile.cpu_brand,
      )
    : undefined;
  const selectedCpu = preferredCpu ?? DEMO_PARTS.cpu;
  const preferredBoard = budgetConstrained
    ? findLowest(
        "motherboard",
        (part) =>
          part.specs.socket === selectedCpu.specs.socket &&
          (profile.form_factor === "any" ||
            part.specs.form_factor === formFactor),
      )
    : undefined;
  const selectedBoard = preferredBoard ?? board;
  const preferredGpu = budgetConstrained
    ? findLowest(
        "gpu",
        (part) =>
          profile.gpu_brand === "any" ||
          part.brand.toLowerCase() === profile.gpu_brand,
      )
    : undefined;
  const selectedGpu = preferredGpu ?? DEMO_PARTS.gpu;
  const selectedMemory =
    budgetConstrained &&
    (selectedBoard.specs as Record<string, unknown>)["memory_type"] === "DDR4"
      ? {
          ...DEMO_PARTS.memory,
          id: "demo-memory-ddr4-entry",
          name: "DDR4 3200 32GB套装",
          brand: "光威",
          specs: { ...DEMO_PARTS.memory.specs, memory_type: "DDR4" },
        }
      : DEMO_PARTS.memory;
  const baseParts = {
    cpu: selectedCpu,
    motherboard: selectedBoard,
    gpu: selectedGpu,
    memory: selectedMemory,
    storage: DEMO_PARTS.storage,
    psu: DEMO_PARTS.psu,
    cooling: DEMO_PARTS.cooling,
    case: casePart,
  };
  return styles.map((style, index) => {
    const items: BuildItem[] = Object.values(baseParts).map((part) => ({
      slot: part.category,
      part,
      locked: false,
      reason: `${part.category === "gpu" ? profile.resolution : "预算与兼容性"} 取向。`,
    }));
    if (index === 0 && !budgetConstrained)
      items.find((item) => item.slot === "gpu")!.part = {
        ...DEMO_PARTS.gpu,
        name: "Radeon RX 7600 8G",
        brand: "AMD",
        price: 2099,
        id: "demo-gpu-value",
        power_w: 165,
      };
    if (index === 2 && !budgetConstrained)
      items.find((item) => item.slot === "memory")!.part = {
        ...DEMO_PARTS.memory,
        name: "DDR5 6000 64GB套装",
        price: 1199,
        id: "demo-memory-performance",
      };
    const total = items.reduce((sum, item) => sum + item.part.price, 0);
    const compatibility = manualPreviewIssues(items);
    if (total > profile.budget) {
      compatibility.push({
        code: "BUDGET_OVER",
        severity: "warning",
        title: "预算不足以覆盖完整配置",
        detail: `当前完整配置参考价约 ${formatMoney(total)} 元，超出预算 ${formatMoney(total - profile.budget)} 元；本地目录未用降价比例伪造平台金额。`,
        related_slots: ["cpu", "motherboard", "gpu", "memory", "storage", "psu", "cooling", "case"],
      });
    }
    return {
      id: `demo-${style}`,
      style,
      title: titles[index],
      summary: summaries[index],
      budget: profile.budget,
      total_price: total,
      estimated_power_w: items.reduce((sum, item) => sum + item.part.power_w, 80),
      performance_score: budgetConstrained
        ? Number(items.find((item) => item.slot === "gpu")?.part.specs.score ?? 60)
        : 78 + index * 10,
      items,
      compatibility,
      created_at: now,
    };
  });
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(
    value,
  );
}

function localInterpret(content: string, current: NeedProfile): NeedProfile {
  const budgetMatch = content.match(/(\d+(?:\.\d+)?)\s*(万|w|W|元|块)?/);
  const next = { ...current };
  if (budgetMatch)
    next.budget = Math.max(
      2500,
      Math.min(
        100000,
        Math.round(
          Number(budgetMatch[1]) *
            (["万", "w", "W"].includes(budgetMatch[2] ?? "") ? 10000 : 1),
        ),
      ),
    );
  if (content.includes("水冷")) next.cooling = "water";
  if (content.includes("风冷")) next.cooling = "air";
  if (/N卡|英伟达|NVIDIA/i.test(content)) next.gpu_brand = "nvidia";
  if (/A卡|AMD显卡|镭/i.test(content)) next.gpu_brand = "amd";
  if (/AMD处理器|锐龙/i.test(content)) next.cpu_brand = "amd";
  if (/Intel|英特尔/i.test(content)) next.cpu_brand = "intel";
  if (content.includes("4K")) next.resolution = "4K";
  if (content.includes("1080")) next.resolution = "1080P";
  if (/剪辑|渲染|生产力/.test(content)) next.use_case = "视频剪辑与生产力";
  if (/mini[- ]?itx|itx|迷你机|小钢炮/i.test(content))
    next.form_factor = "Mini-ITX";
  else if (/m[- ]?atx|matx|micro[- ]?atx|小机箱|紧凑/i.test(content))
    next.form_factor = "mATX";
  else if (/atx|标准机箱/i.test(content)) next.form_factor = "ATX";
  return next;
}

function localConversation(profile: NeedProfile): ConversationResponse {
  return {
    id: `local-${Date.now()}`,
    profile,
    messages: [
      {
        role: "assistant",
        content: "你好，我会先了解你的用途和预算，再给出几套可解释的装机方案。",
        created_at: new Date().toISOString(),
      },
    ],
  };
}

function tierClass(tier: string) {
  return `tier-badge tier-${tier.toLowerCase()}`;
}

const COMPATIBILITY_CHECKS = [
  { code: "CPU_SOCKET", label: "CPU / 主板插槽" },
  { code: "MEMORY_TYPE", label: "内存代际" },
  { code: "FORM_FACTOR", label: "主板 / 机箱尺寸" },
  { code: "GPU_LENGTH", label: "显卡长度" },
  { code: "COOLER_HEIGHT", label: "风冷高度" },
  { code: "RADIATOR_SIZE", label: "冷排尺寸" },
  { code: "COOLER_SOCKET", label: "散热器扣具" },
  { code: "STORAGE_INTERFACE", label: "硬盘接口 / 插槽" },
  { code: "GPU_POWER_CONNECTOR", label: "显卡供电接口" },
  { code: "PSU_HEADROOM", label: "电源功率余量" },
];

function manualPreviewIssues(items: BuildItem[]): CompatibilityIssue[] {
  const bySlot = new Map(items.map((item) => [item.slot, item.part]));
  const spec = (slot: PartCategory, key: string) =>
    bySlot.get(slot)?.specs[key];
  const warning = (
    code: string,
    title: string,
    detail: string,
    related_slots: PartCategory[],
  ): CompatibilityIssue => ({
    code,
    severity: "warning",
    title,
    detail,
    related_slots,
  });
  const error = (
    code: string,
    title: string,
    detail: string,
    related_slots: PartCategory[],
  ): CompatibilityIssue => ({
    code,
    severity: "error",
    title,
    detail,
    related_slots,
  });
  const issues: CompatibilityIssue[] = [];

  const cpuSocket = spec("cpu", "socket");
  const boardSocket = spec("motherboard", "socket");
  if (!cpuSocket || !boardSocket)
    issues.push(
      warning(
        "CPU_SOCKET_UNKNOWN",
        "CPU / 主板插槽待确认",
        "缺少插槽字段，生成方案后需要补充核对。",
        ["cpu", "motherboard"],
      ),
    );
  else if (cpuSocket !== boardSocket)
    issues.push(
      error(
        "CPU_SOCKET_MISMATCH",
        "CPU / 主板插槽不兼容",
        `处理器为 ${String(cpuSocket)}，主板为 ${String(boardSocket)}。`,
        ["cpu", "motherboard"],
      ),
    );

  const memoryType = spec("memory", "memory_type");
  const boardMemory = spec("motherboard", "memory_type");
  if (!memoryType || !boardMemory)
    issues.push(
      warning(
        "MEMORY_TYPE_UNKNOWN",
        "内存代际待确认",
        "缺少内存或主板代际字段。",
        ["memory", "motherboard"],
      ),
    );
  else if (memoryType !== boardMemory)
    issues.push(
      error(
        "MEMORY_TYPE_MISMATCH",
        "内存代际不兼容",
        `内存为 ${String(memoryType)}，主板支持 ${String(boardMemory)}。`,
        ["memory", "motherboard"],
      ),
    );

  const boardForm = spec("motherboard", "form_factor");
  const caseForms = spec("case", "supported_form_factors");
  if (!boardForm || !Array.isArray(caseForms))
    issues.push(
      warning(
        "FORM_FACTOR_UNKNOWN",
        "机箱尺寸待确认",
        "缺少主板或机箱板型字段。",
        ["motherboard", "case"],
      ),
    );
  else if (!caseForms.includes(boardForm))
    issues.push(
      error(
        "FORM_FACTOR_MISMATCH",
        "主板无法安装进机箱",
        `机箱不支持 ${String(boardForm)} 主板。`,
        ["motherboard", "case"],
      ),
    );

  const gpuLength = Number(spec("gpu", "length_mm"));
  const caseGpuLength = Number(spec("case", "gpu_length_mm"));
  if (!gpuLength || !caseGpuLength)
    issues.push(
      warning(
        "GPU_LENGTH_UNKNOWN",
        "显卡长度待确认",
        "缺少显卡长度或机箱限长字段。",
        ["gpu", "case"],
      ),
    );
  else if (gpuLength > caseGpuLength)
    issues.push(
      error(
        "GPU_LENGTH_EXCEEDED",
        "显卡长度超限",
        `显卡 ${gpuLength}mm，机箱限长 ${caseGpuLength}mm。`,
        ["gpu", "case"],
      ),
    );

  const coolingType = spec("cooling", "type");
  const coolerHeight = Number(spec("cooling", "height_mm"));
  const caseCoolerHeight = Number(spec("case", "cooler_height_mm"));
  if (coolingType === "air" && (!coolerHeight || !caseCoolerHeight))
    issues.push(
      warning(
        "COOLER_HEIGHT_UNKNOWN",
        "风冷高度待确认",
        "缺少散热器高度或机箱限高字段。",
        ["cooling", "case"],
      ),
    );
  else if (coolingType === "air" && coolerHeight > caseCoolerHeight)
    issues.push(
      error(
        "COOLER_HEIGHT_EXCEEDED",
        "风冷高度超限",
        `散热器 ${coolerHeight}mm，机箱限高 ${caseCoolerHeight}mm。`,
        ["cooling", "case"],
      ),
    );

  const radiator = Number(spec("cooling", "radiator_mm"));
  const caseRadiator = Number(spec("case", "radiator_mm"));
  if (coolingType === "water" && (!radiator || !caseRadiator))
    issues.push(
      warning(
        "RADIATOR_SIZE_UNKNOWN",
        "冷排尺寸待确认",
        "缺少冷排或机箱支持尺寸字段。",
        ["cooling", "case"],
      ),
    );
  else if (coolingType === "water" && radiator > caseRadiator)
    issues.push(
      error(
        "RADIATOR_SIZE_EXCEEDED",
        "冷排尺寸超限",
        `冷排 ${radiator}mm，机箱支持到 ${caseRadiator}mm。`,
        ["cooling", "case"],
      ),
    );

  const sockets = spec("cooling", "supported_sockets");
  if (!Array.isArray(sockets) || !cpuSocket)
    issues.push(
      warning(
        "COOLER_SOCKET_UNKNOWN",
        "散热器扣具待确认",
        "缺少散热器支持平台字段。",
        ["cooling", "cpu"],
      ),
    );
  else if (!sockets.includes(cpuSocket))
    issues.push(
      error(
        "COOLER_SOCKET_MISMATCH",
        "散热器扣具不兼容",
        `散热器不支持 ${String(cpuSocket)}。`,
        ["cooling", "cpu"],
      ),
    );

  const storageConnector = spec("storage", "connector");
  const m2Slots = Number(spec("motherboard", "m2_slots"));
  const sataPorts = Number(spec("motherboard", "sata_ports"));
  if (!storageConnector)
    issues.push(
      warning(
        "STORAGE_INTERFACE_UNKNOWN",
        "硬盘接口待确认",
        "缺少硬盘物理接口字段。",
        ["storage", "motherboard"],
      ),
    );
  else if (storageConnector === "M.2" && !m2Slots)
    issues.push(
      error(
        "STORAGE_INTERFACE_MISMATCH",
        "主板缺少 M.2 插槽",
        "当前硬盘需要 M.2 插槽。",
        ["storage", "motherboard"],
      ),
    );
  else if (storageConnector === "SATA" && !sataPorts)
    issues.push(
      error(
        "STORAGE_INTERFACE_MISMATCH",
        "主板缺少 SATA 接口",
        "当前硬盘需要 SATA 接口。",
        ["storage", "motherboard"],
      ),
    );

  const powerConnectors = spec("gpu", "power_connectors");
  if (!Array.isArray(powerConnectors))
    issues.push(
      warning(
        "GPU_POWER_CONNECTOR_UNKNOWN",
        "显卡供电待确认",
        "缺少显卡供电接口字段。",
        ["gpu", "psu"],
      ),
    );
  else if (powerConnectors.includes("12VHPWR") && !spec("psu", "twelve_vhpwr"))
    issues.push(
      warning(
        "GPU_POWER_CONNECTOR_ADAPTER",
        "显卡供电需转接",
        "显卡需要 12VHPWR，当前电源未标记原生接口。",
        ["gpu", "psu"],
      ),
    );

  const wattage = Number(spec("psu", "wattage"));
  const estimatedPower = items.reduce(
    (sum, item) => sum + item.part.power_w,
    80,
  );
  if (!wattage)
    issues.push(
      warning(
        "PSU_HEADROOM_UNKNOWN",
        "电源余量待确认",
        "缺少电源额定功率字段。",
        ["psu"],
      ),
    );
  else if (wattage < Math.ceil(estimatedPower * 1.2))
    issues.push(
      error(
        "PSU_HEADROOM_LOW",
        "电源余量不足",
        `预计功耗 ${estimatedPower}W，建议至少预留 20% 余量。`,
        ["psu"],
      ),
    );
  return issues;
}

function CompatibilityChecklist({ issues }: { issues: CompatibilityIssue[] }) {
  return (
    <section className="compatibility-checklist" aria-label="兼容性检查清单">
      <div className="checklist-head">
        <div>
          <span className="eyebrow">装机检查</span>
          <h5>逐项核对</h5>
        </div>
        <span>{COMPATIBILITY_CHECKS.length} 项规则</span>
      </div>
      <div className="compatibility-check-grid">
        {COMPATIBILITY_CHECKS.map((check) => {
          const issue = issues.find(
            (item) =>
              item.code === check.code ||
              item.code.startsWith(`${check.code}_`),
          );
          const status = issue?.severity ?? "ok";
          return (
            <div
              className={`compatibility-check-row ${status}`}
              key={check.code}
            >
              {status === "error" ? (
                <X size={15} />
              ) : status === "warning" ? (
                <RefreshCw size={15} />
              ) : (
                <CheckCircle2 size={15} />
              )}
              <div>
                <strong>{check.label}</strong>
                <small>{issue?.detail ?? "已通过"}</small>
              </div>
              <span>
                {status === "error"
                  ? "需调整"
                  : status === "warning"
                    ? "待确认"
                    : "通过"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function RequirementColumn({
  title,
  data,
}: {
  title: string;
  data: SystemRequirement;
}) {
  const rows = [
    ["系统", data.operating_system],
    ["处理器", data.processor],
    ["内存", data.memory_gb ? `${data.memory_gb} GB` : "未提供"],
    ["显卡", data.graphics],
    ["DirectX", data.directx ?? "未提供"],
    ["存储", data.storage_gb ? `${data.storage_gb} GB 可用空间` : "未提供"],
    ...(data.additional_notes ? [["补充", data.additional_notes]] : []),
  ];
  return (
    <div className="requirement-column">
      <div className="requirement-title">
        <span>{title}</span>
        <span className="requirement-mark">
          {title === "推荐配置" ? "建议" : "起步"}
        </span>
      </div>
      {rows.map(([label, value]) => (
        <div className="requirement-row" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<AppView>("builder");
  const [theme, setTheme] = useState<Theme>("corporate");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [profile, setProfile] = useState<NeedProfile>(DEFAULT_PROFILE);
  const [conversation, setConversation] = useState<ConversationResponse | null>(
    null,
  );
  const [plans, setPlans] = useState<BuildPlan[]>(() =>
    demoPlans(DEFAULT_PROFILE),
  );
  const [activePlanId, setActivePlanId] = useState("demo-balanced");
  const [message, setMessage] = useState("");
  const [budgetDraft, setBudgetDraft] = useState(String(DEFAULT_PROFILE.budget));
  const [notice, setNotice] = useState(
    "演示模式已就绪；启动 API 和 Worker 后可刷新真实任务与导出。",
  );
  const [generationFeedback, setGenerationFeedback] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobMessage, setJobMessage] = useState("准备中");
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [recommendationPlanId, setRecommendationPlanId] = useState<string | null>(null);
  const [recommendationBusy, setRecommendationBusy] = useState(false);
  const [recommendationError, setRecommendationError] = useState("");
  const [recommendationProgress, setRecommendationProgress] = useState(0);
  const [recommendationMessage, setRecommendationMessage] = useState("准备中");
  const [demoMode, setDemoMode] = useState(true);
  const [ladderCategory, setLadderCategory] = useState<LadderCategory>("gpu");
  const [ladderItems, setLadderItems] = useState<HardwareLadderEntry[]>(
    LOCAL_LADDER_ITEMS.filter((item) => item.category === "gpu"),
  );
  const [ladderQuery, setLadderQuery] = useState("");
  const [ladderBrand, setLadderBrand] = useState("all");
  const [ladderMinPrice, setLadderMinPrice] = useState("");
  const [ladderMaxPrice, setLadderMaxPrice] = useState("");
  const [pickerSlot, setPickerSlot] = useState<PartCategory | null>(null);
  const [pickerItems, setPickerItems] = useState<Part[]>([]);
  const [pickerInitialPartId, setPickerInitialPartId] = useState<string>();
  const [pickerBusy, setPickerBusy] = useState(false);
  const [pickerSync, setPickerSync] = useState<CatalogSyncStatus | null>(null);
  const [pickerSyncProgress, setPickerSyncProgress] = useState(0);
  const [pickerOffers, setPickerOffers] = useState<Offer[]>([]);
  const [pickerOffersBusy, setPickerOffersBusy] = useState(false);
  const [productDetail, setProductDetail] = useState<ProductDetail | null>(
    null,
  );
  const [gameQuery, setGameQuery] = useState("");
  const [gameResults, setGameResults] = useState<GameSearchResult[]>(
    Object.values(LOCAL_GAMES).map(({ app_id, name, source }) => ({
      app_id,
      name,
      source,
    })),
  );
  const [gameRequirement, setGameRequirement] =
    useState<GameRequirement | null>(null);
  const [gameBusy, setGameBusy] = useState(false);
  const stopStream = useRef<(() => void) | null>(null);
  const recommendationStopStream = useRef<(() => void) | null>(null);
  const recommendationRequestId = useRef(0);
  const catalogStopStream = useRef<(() => void) | null>(null);
  const activePickerSlot = useRef<PartCategory | null>(null);
  const pickerOfferRequest = useRef(0);
  const hasUserInteracted = useRef(false);

  useEffect(() => {
    let active = true;
    api
      .createConversation(DEFAULT_PROFILE)
      .then((result) => {
        if (!active) return;
        setConversation(result);
        setDemoMode(false);
        if (!hasUserInteracted.current) {
          setProfile(result.profile);
          setBudgetDraft(String(result.profile.budget));
        }
        setNotice("已连接到本地 API");
      })
      .catch(() => {
        if (active && !hasUserInteracted.current)
          setConversation(localConversation(DEFAULT_PROFILE));
      });
    return () => {
      active = false;
      stopStream.current?.();
      recommendationStopStream.current?.();
      catalogStopStream.current?.();
    };
  }, []);

  useEffect(() => {
    if (view !== "ladder") return undefined;
    let active = true;
    api
      .getLadder(ladderCategory)
      .then((result) => {
        if (active && result.items.length) setLadderItems(result.items);
      })
      .catch(() => {
        if (active)
          setLadderItems(
            LOCAL_LADDER_ITEMS.filter(
              (item) => item.category === ladderCategory,
            ),
          );
      });
    return () => {
      active = false;
    };
  }, [ladderCategory, view]);

  useEffect(() => {
    if (!productDetail) return;
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [productDetail]);

  const activePlan = useMemo(
    () => plans.find((plan) => plan.id === activePlanId) ?? plans[1],
    [activePlanId, plans],
  );
  const errors =
    activePlan?.compatibility.filter((item) => item.severity === "error") ?? [];
  const warnings =
    activePlan?.compatibility.filter((item) => item.severity === "warning") ??
    [];
  const budgetIssue = activePlan?.compatibility.find(
    (item) => item.code === "BUDGET_OVER",
  );

  async function requestRecommendationForPlan(
    targetPlan: BuildPlan,
    profileForPlan: NeedProfile = profile,
    gameRequirementForPlan: GameRequirement | null = gameRequirement,
  ) {
    const requestId = ++recommendationRequestId.current;
    recommendationStopStream.current?.();
    recommendationStopStream.current = null;
    setRecommendationPlanId(targetPlan.id);
    setRecommendation(null);
    setRecommendationError("");
    setRecommendationBusy(true);
    setRecommendationProgress(8);
    setRecommendationMessage("准备整理需求与配置依据");
    try {
      if (demoMode || targetPlan.id.startsWith("demo-")) {
        await new Promise((resolve) => window.setTimeout(resolve, 420));
        if (requestId === recommendationRequestId.current) {
          setRecommendation(
            createOfflineRecommendation(
              targetPlan,
              profileForPlan,
              gameRequirementForPlan,
            ),
          );
          setRecommendationProgress(100);
          setRecommendationMessage("已完成");
        }
        return;
      }
      const job = await api.generateRecommendation(targetPlan.id, {
        gameAppId: gameRequirementForPlan?.app_id,
        includeCommunityEvidence: true,
      });
      recommendationStopStream.current = streamJob(
        job.id,
        (event) => {
          if (requestId !== recommendationRequestId.current) return;
          setRecommendationProgress(event.progress);
          setRecommendationMessage(event.message);
        },
        () => undefined,
      );
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const current = await api.getJob(job.id);
        if (requestId !== recommendationRequestId.current) return;
        setRecommendationProgress(current.progress);
        setRecommendationMessage(current.message);
        if (current.status === "completed") {
          let result = current.result?.recommendation;
          if (!result && current.result?.recommendation_id) {
            result = await api.getRecommendation(current.result.recommendation_id);
          }
          if (!result) throw new Error("建议结果为空，请稍后重试");
          setRecommendation(result);
          setRecommendationProgress(100);
          setRecommendationMessage("已完成");
          return;
        }
        if (["dead_letter", "cancelled"].includes(current.status)) {
          throw new Error(current.error ?? "建议任务未完成");
        }
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }
      throw new Error("建议等待超时，请确认 Worker 已启动");
    } catch (error) {
      if (requestId === recommendationRequestId.current) {
        setRecommendationError(error instanceof Error ? error.message : "建议生成失败，请稍后重试");
      }
    } finally {
      if (requestId === recommendationRequestId.current) setRecommendationBusy(false);
    }
  }

  const ladderBrands = useMemo(
    () => Array.from(new Set(ladderItems.map((item) => item.brand))).sort(),
    [ladderItems],
  );
  const filteredLadder = useMemo(() => {
    const needle = ladderQuery.trim().toLowerCase();
    const low = ladderMinPrice ? Number(ladderMinPrice) : undefined;
    const high = ladderMaxPrice ? Number(ladderMaxPrice) : undefined;
    return ladderItems.filter((item) => {
      if (
        needle &&
        !`${item.name} ${item.brand} ${item.note}`
          .toLowerCase()
          .includes(needle)
      )
        return false;
      if (ladderBrand !== "all" && item.brand !== ladderBrand) return false;
      if (low !== undefined && (item.reference_price ?? 0) < low) return false;
      if (high !== undefined && (item.reference_price ?? 0) > high)
        return false;
      return true;
    });
  }, [ladderBrand, ladderItems, ladderMaxPrice, ladderMinPrice, ladderQuery]);
  const groupedLadder = useMemo(
    () =>
      ["S", "A", "B", "C"]
        .map((tier) => ({
          tier,
          items: filteredLadder.filter((item) => item.tier === tier),
        }))
        .filter((group) => group.items.length),
    [filteredLadder],
  );

  const updateProfile = <K extends keyof NeedProfile>(
    key: K,
    value: NeedProfile[K],
  ) => {
    setProfile((current) => ({ ...current, [key]: value }));
    setRecommendation(null);
    setRecommendationPlanId(null);
    setRecommendationError("");
    if (key === "budget") setBudgetDraft(String(value));
  };

  const commitBudgetDraft = () => {
    const amount = Number(budgetDraft);
    const nextBudget = Number.isFinite(amount)
      ? normalizeBudget(amount)
      : profile.budget;
    setBudgetDraft(String(nextBudget));
    updateProfile("budget", nextBudget);
  };

  function revealGeneratedPlans() {
    const target = document.getElementById("plans-workbench");
    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function applyMentionedGame(game: GameRequirement | null) {
    if (!game) return;
    setGameQuery(game.name);
    setGameRequirement(game);
    setGameResults([{ app_id: game.app_id, name: game.name, source: game.source }]);
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (isGenerating || recommendationBusy) return;
    const content = message.trim();
    if (!content) return;
    hasUserInteracted.current = true;
    recommendationStopStream.current?.();
    recommendationRequestId.current += 1;
    setRecommendation(null);
    setRecommendationPlanId(null);
    setRecommendationError("");
    setMessage("");
    setIsGenerating(true);
    setJobProgress(4);
    setJobMessage("正在接收需求");
    setGenerationFeedback("");
    const mentionedGame = findMentionedGame(content);
    const parsedDraftBudget = Number(budgetDraft);
    const profileForInterpretation: NeedProfile = Number.isFinite(parsedDraftBudget)
      ? { ...profile, budget: normalizeBudget(parsedDraftBudget) }
      : profile;
    const next = localInterpret(content, profileForInterpretation);
    const nextGame = mentionedGame ?? gameRequirement;
    let nextConversation = conversation;
    let forceLocalGeneration = demoMode || !conversation;

    if (!forceLocalGeneration && conversation) {
      try {
        nextConversation = await api.sendMessage(conversation.id, content);
        setConversation(nextConversation);
        setProfile(next);
        setBudgetDraft(String(next.budget));
        applyMentionedGame(mentionedGame);
        setNotice(
          mentionedGame
            ? `已识别游戏：${mentionedGame.name}，正在生成可核对方案`
            : "需求已更新，正在生成可核对方案",
        );
      } catch {
        forceLocalGeneration = true;
        setDemoMode(true);
        setNotice("API 暂不可用，正在使用本地可核对方案");
      }
    }

    setProfile(next);
    setBudgetDraft(String(next.budget));
    applyMentionedGame(mentionedGame);

    if (forceLocalGeneration) {
      setConversation((current) => ({
        ...(current ?? localConversation(profile)),
        profile: next,
        messages: [
          ...(current?.messages ?? []),
          { role: "user", content, created_at: new Date().toISOString() },
          {
            role: "assistant",
            content: `收到：预算约 ${formatMoney(next.budget)} 元，目标 ${next.resolution}。${
              mentionedGame
                ? `已识别游戏：${mentionedGame.name}，最低/推荐配置已载入。`
                : ""
            }正在生成可核对方案，完成后会进入方案工作台。`,
            created_at: new Date().toISOString(),
          },
        ],
      }));
    }

    await handleGenerate(
      next,
      nextConversation,
      nextGame,
      forceLocalGeneration,
    );
  }

  async function handleGenerate(
    profileOverride?: NeedProfile,
    conversationOverride?: ConversationResponse | null,
    gameRequirementOverride?: GameRequirement | null,
    forceLocal = false,
  ) {
    const profileBase = profileOverride ?? profile;
    const parsedBudget = Number(budgetDraft);
    const effectiveProfile: NeedProfile = profileOverride
      ? { ...profileBase, budget: normalizeBudget(profileBase.budget) }
      : {
          ...profileBase,
          budget: Number.isFinite(parsedBudget)
            ? normalizeBudget(parsedBudget)
            : profileBase.budget,
        };
    const targetConversation =
      conversationOverride === undefined ? conversation : conversationOverride;
    const targetGame =
      gameRequirementOverride === undefined
        ? gameRequirement
        : gameRequirementOverride;
    setProfile(effectiveProfile);
    setBudgetDraft(String(effectiveProfile.budget));
    recommendationStopStream.current?.();
    recommendationRequestId.current += 1;
    setRecommendation(null);
    setRecommendationPlanId(null);
    setRecommendationError("");
    setIsGenerating(true);
    setJobProgress(12);
    setJobMessage("读取需求");
    setGenerationFeedback("");
    let onlineJobStarted = false;

    const completeOfflineGeneration = async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 650));
      setJobProgress(100);
      setJobMessage("已完成");
      const nextPlans = demoPlans(effectiveProfile);
      setPlans(nextPlans);
      setActivePlanId("demo-balanced");
      const nextActivePlan =
        nextPlans.find((plan) => plan.id === "demo-balanced") ?? nextPlans[1];
      if (nextActivePlan)
        void requestRecommendationForPlan(
          nextActivePlan,
          effectiveProfile,
          targetGame,
        );
      setNotice("三套方案已生成（本地演示）");
      setGenerationFeedback("三套方案已生成（本地演示），已更新到方案工作台");
      revealGeneratedPlans();
    };

    try {
      if (!forceLocal && !demoMode && targetConversation) {
        const updatedConversation = await api.updateProfile(
          targetConversation.id,
          effectiveProfile,
        );
        setConversation(updatedConversation);
        const job = await api.generate(updatedConversation.id);
        onlineJobStarted = true;
        stopStream.current = streamJob(
          job.id,
          (event) => {
            setJobProgress(event.progress);
            setJobMessage(event.message);
          },
          () => undefined,
        );
        for (let attempt = 0; attempt < 40; attempt += 1) {
          const current = await api.getJob(job.id);
          setJobProgress(current.progress);
          setJobMessage(current.message);
          if (current.status === "completed") {
            const nextPlans =
              current.result?.plans ??
              (await api.getPlans(updatedConversation.id)).plans;
            setPlans(nextPlans);
            const nextActivePlan = nextPlans[1] ?? nextPlans[0];
            setActivePlanId(nextActivePlan?.id ?? activePlanId);
            if (nextActivePlan)
              void requestRecommendationForPlan(
                nextActivePlan,
                effectiveProfile,
                targetGame,
              );
            setNotice("三套方案已生成");
            setGenerationFeedback("三套方案已生成，已更新到方案工作台");
            revealGeneratedPlans();
            return;
          }
          if (["dead_letter", "cancelled"].includes(current.status))
            throw new Error(current.error ?? "任务未完成");
          await new Promise((resolve) => window.setTimeout(resolve, 500));
        }
        throw new Error("任务等待超时，请确认 Worker 已启动");
      }
      await completeOfflineGeneration();
    } catch (error) {
      if (profileOverride && !forceLocal && !onlineJobStarted) {
        setDemoMode(true);
        setNotice("在线服务暂不可用，已切换本地可核对方案");
        setGenerationFeedback("在线服务暂不可用，已使用本地可核对方案");
        await completeOfflineGeneration();
      } else {
        const message = error instanceof Error ? error.message : "生成失败，请稍后重试";
        setNotice(message);
        setGenerationFeedback(message);
        setJobMessage("生成失败");
      }
    } finally {
      setIsGenerating(false);
    }
  }

  async function loadPickerOffers(part: Part) {
    const requestId = ++pickerOfferRequest.current;
    setPickerOffers([]);
    setPickerOffersBusy(true);
    try {
      const detail = await api.getProduct(part.id);
      if (
        requestId === pickerOfferRequest.current &&
        activePickerSlot.current === part.category
      ) {
        setPickerOffers(detail.offers);
      }
    } catch {
      if (
        requestId === pickerOfferRequest.current &&
        activePickerSlot.current === part.category
      ) {
        setPickerOffers(localProductDetail(part).offers);
        setNotice("平台报价接口暂不可用，已保留京东与拼多多搜索入口；价格待联网");
      }
    } finally {
      if (requestId === pickerOfferRequest.current) setPickerOffersBusy(false);
    }
  }

  async function openPartPicker(
    slot: PartCategory,
    initialPartId?: string,
    initialPartName?: string,
  ) {
    activePickerSlot.current = slot;
    setPickerSlot(slot);
    setPickerInitialPartId(initialPartId);
    setPickerSync(null);
    setPickerSyncProgress(0);
    pickerOfferRequest.current += 1;
    setPickerOffers([]);
    setPickerOffersBusy(false);
    const localItems = LOCAL_CATALOG.filter((part) => part.category === slot);
    setPickerItems(localItems);
    const localMatch = localItems.find(
      (part) =>
        part.id === initialPartId ||
        (initialPartName && part.name === initialPartName),
    );
    if (localMatch) setPickerInitialPartId(localMatch.id);
    const localSelection = localMatch ?? localItems[0];
    if (localSelection) void loadPickerOffers(localSelection);
    setPickerBusy(true);
    try {
      const catalog = await api.getCatalog(slot);
      setPickerSync(catalog.sync);
      if (catalog.items.length) {
        setPickerItems(catalog.items);
        const match = catalog.items.find(
          (part) =>
            part.id === initialPartId ||
            (initialPartName && part.name === initialPartName),
        );
        const selectedPart = match ?? catalog.items[0];
        setPickerInitialPartId(selectedPart.id);
        void loadPickerOffers(selectedPart);
      }
      if (
        catalog.sync.enabled &&
        catalog.sync.stale &&
        !["queued", "running"].includes(catalog.sync.status)
      ) {
        void refreshPickerCatalog(slot, true);
      }
    } catch {
      setNotice("配件接口未连接，已显示本地参考数据");
    } finally {
      setPickerBusy(false);
    }
  }

  async function refreshPickerCatalog(
    slot: PartCategory,
    automatic = false,
  ) {
    catalogStopStream.current?.();
    setPickerSyncProgress(0);
    setPickerSync((current) => ({
      enabled: true,
      status: "queued",
      provider: current?.provider ?? "ZOL 公开产品目录",
      item_count: current?.item_count ?? 0,
      message: automatic ? "正在后台补充具体厂商型号" : "目录更新已进入后台队列",
      updated_at: current?.updated_at,
      stale: true,
      source_url: current?.source_url,
    }));
    try {
      const job = await api.refreshCatalog(slot);
      catalogStopStream.current = streamJob(
        job.id,
        (event) => {
          if (activePickerSlot.current !== slot) return;
          setPickerSyncProgress(event.progress);
          setPickerSync((current) =>
            current
              ? {
                  ...current,
                  status: event.status,
                  message: event.message,
                }
              : current,
          );
        },
        () => {
          void api
            .getCatalog(slot)
            .then((catalog) => {
              if (activePickerSlot.current !== slot) return;
              setPickerItems(catalog.items);
              setPickerSync(catalog.sync);
              setPickerSyncProgress(100);
              if (catalog.sync.status === "completed") {
                setNotice(`已补充 ${catalog.sync.item_count} 个公开厂商型号`);
              }
            })
            .catch(() => {
              if (activePickerSlot.current === slot) {
                setNotice("目录更新状态读取失败，当前候选仍可继续使用");
              }
            });
        },
      );
    } catch (error) {
      setPickerSync((current) =>
        current
          ? {
              ...current,
              status: "unavailable",
              message: "更新暂不可用，继续展示本地与缓存候选",
            }
          : current,
      );
      if (!automatic) {
        setNotice(error instanceof Error ? error.message : "目录更新失败");
      }
    }
  }

  function handleSwap(item: BuildItem) {
    void openPartPicker(item.slot, item.part.id, item.part.name);
  }

  async function openProductDetail(part: Part) {
    setPickerBusy(true);
    try {
      setProductDetail(await api.getProduct(part.id));
      setNotice("已打开商品详情；平台金额会区分实时、公开参考与待联网状态");
    } catch {
      setProductDetail(localProductDetail(part));
      setNotice("商品详情接口未连接，已显示离线参数与平台搜索入口");
    } finally {
      setPickerBusy(false);
    }
  }

  async function handleUsePart(part: Part) {
    if (!pickerSlot || !activePlan) return;
    setPickerBusy(true);
    recommendationStopStream.current?.();
    recommendationRequestId.current += 1;
    setRecommendation(null);
    setRecommendationPlanId(null);
    setRecommendationError("");
    try {
      const currentItem = activePlan.items.find(
        (item) => item.slot === pickerSlot,
      );
      if (!activePlan.id.startsWith("demo-")) {
        const updated = await api.replaceItem(
          activePlan.id,
          pickerSlot,
          part.id,
          currentItem?.locked ?? false,
        );
        setPlans((current) =>
          current.map((plan) => (plan.id === updated.id ? updated : plan)),
        );
        setNotice(`${SLOT_LABELS[pickerSlot]}已选入，兼容性已重新计算`);
      } else {
        setPlans((current) =>
          current.map((plan) => {
            if (plan.id !== activePlan.id) return plan;
            const items = plan.items.map((item) =>
              item.slot === pickerSlot
                ? { ...item, part, reason: "用户手动选择" }
                : item,
            );
            return {
              ...plan,
              items,
              total_price: items.reduce(
                (sum, item) => sum + item.part.price,
                0,
              ),
              estimated_power_w: items.reduce(
                (sum, item) => sum + item.part.power_w,
                80,
              ),
              compatibility: manualPreviewIssues(items),
            };
          }),
        );
        setNotice(
          `${SLOT_LABELS[pickerSlot]}已选入预览；请生成方案完成兼容性复核`,
        );
      }
      setPickerSlot(null);
      activePickerSlot.current = null;
      pickerOfferRequest.current += 1;
      setPickerOffers([]);
      setPickerOffersBusy(false);
      setProductDetail(null);
    } catch {
      setNotice("选入失败，请确认方案已生成且配件仍可用");
    } finally {
      setPickerBusy(false);
    }
  }

  async function handleLock(item: BuildItem) {
    recommendationStopStream.current?.();
    recommendationRequestId.current += 1;
    setRecommendation(null);
    setRecommendationPlanId(null);
    setRecommendationError("");
    try {
      if (!demoMode && activePlan && !activePlan.id.startsWith("demo-"))
        await api.replaceItem(
          activePlan.id,
          item.slot,
          item.part.id,
          !item.locked,
        );
    } catch {
      setNotice("锁定状态同步失败");
    }
    setPlans((current) =>
      current.map((plan) =>
        plan.id === activePlan?.id
          ? {
              ...plan,
              items: plan.items.map((entry) =>
                entry.slot === item.slot
                  ? { ...entry, locked: !entry.locked }
                  : entry,
              ),
            }
          : plan,
      ),
    );
  }

  async function handleExport() {
    if (demoMode || !activePlan || activePlan.id.startsWith("demo-")) {
      setNotice("当前是演示预览，请先提交需求或点击“重新生成并核对”再导出 Excel");
      return;
    }
    try {
      const job = await api.exportPlan(activePlan.id);
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const current = await api.getJob(job.id);
        if (current.status === "completed") {
          window.open(
            `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/jobs/${job.id}/download`,
            "_blank",
          );
          setNotice("Excel 清单已准备完成");
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }
      setNotice("导出等待超时，请确认 Worker 已启动");
    } catch {
      setNotice("导出失败，请稍后重试");
    }
  }

  async function handleGameSearch(event: FormEvent) {
    event.preventDefault();
    const query = gameQuery.trim();
    setGameBusy(true);
    try {
      const result = await api.searchGames(query);
      setGameResults(result.items);
      if (!result.items.length) setGameRequirement(null);
    } catch {
      const results = searchLocalGames(query);
      setGameResults(results);
      setNotice("Steam 查询接口未连接，已显示本地示例数据");
    } finally {
      setGameBusy(false);
    }
  }

  async function selectGame(game: GameSearchResult) {
    setGameBusy(true);
    try {
      setGameRequirement(await api.getGameRequirements(game.app_id));
    } catch {
      setGameRequirement(LOCAL_GAMES[game.app_id] ?? null);
    } finally {
      setGameBusy(false);
    }
  }

  const budgetDraftValidation = budgetValidationMessage(budgetDraft);
  const budgetDraftHasError = !budgetDraftValidation.startsWith("支持");

  function closePicker() {
    catalogStopStream.current?.();
    activePickerSlot.current = null;
    pickerOfferRequest.current += 1;
    setPickerOffers([]);
    setPickerOffersBusy(false);
    setPickerSlot(null);
  }

  const renderPicker = () =>
    pickerSlot ? (
      <PartPicker
        slot={pickerSlot}
        items={pickerItems}
        initialPartId={pickerInitialPartId}
        busy={pickerBusy}
        sync={pickerSync}
        syncProgress={pickerSyncProgress}
        onClose={() => {
          closePicker();
        }}
        onUse={handleUsePart}
        offers={pickerOffers}
        offersBusy={pickerOffersBusy}
        onSelect={loadPickerOffers}
        onViewDetails={(part) => void openProductDetail(part)}
        onRefresh={() => refreshPickerCatalog(pickerSlot)}
      />
    ) : null;

  const renderBuilder = () => (
    <>
      <section className="hero-card glass-card">
        <div className="hero-copy">
          <span className="hero-kicker">
            <Sparkles size={15} /> PC SETUP WORKBENCH
          </span>
          <h2>先说需求，剩下的交给我。</h2>
          <p>
            预算、用途、分辨率和偏好，变成一套能装、能解释、能继续调整的配置。
          </p>
        </div>
        <form className="hero-query" onSubmit={handleSend}>
          <label htmlFor="hero-query-input">描述你的装机需求</label>
          <div className="query-row">
            <input
              id="hero-query-input"
              aria-label="输入你的装机需求"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="例如：8000 元，主要玩 2K 游戏，希望安静一些"
            />
            <button
              className="gold-button"
              aria-label="提交需求并生成可核对方案"
              type="submit"
              disabled={isGenerating || recommendationBusy}
            >
              <Send size={18} />
              {isGenerating || recommendationBusy
                ? "正在生成可核对方案"
                : "告诉我并生成可核对方案"}
            </button>
          </div>
          <div className="quick-prompts">
            <span>快速开始</span>
            <button
              type="button"
              onClick={() => setMessage("预算 8000，想要 2K 游戏，N卡，风冷")}
            >
              2K 游戏方案
            </button>
            <button
              type="button"
              onClick={() => setMessage("我比较在意安静和后续升级")}
            >
              安静与升级
            </button>
          </div>
          <RequestInsightPanel
            profile={profile}
            gameRequirement={gameRequirement}
            recommendation={
              recommendationPlanId === activePlan?.id ? recommendation : null
            }
            plan={activePlan}
            busy={recommendationBusy && recommendationPlanId === activePlan?.id}
            planBusy={isGenerating}
            progress={
              isGenerating
                ? jobProgress
                : recommendationPlanId === activePlan?.id
                  ? recommendationProgress
                  : 0
            }
            message={
              isGenerating
                ? jobMessage
                : recommendationPlanId === activePlan?.id
                  ? recommendationMessage
                  : ""
            }
            error={recommendationPlanId === activePlan?.id ? recommendationError : ""}
            onGenerate={() => void handleGenerate()}
            onViewResult={revealGeneratedPlans}
          />
        </form>
      </section>
      <main className="builder-grid">
        <aside className="needs-panel glass-card">
          <div className="section-head">
            <div>
              <span className="eyebrow">01 / 需求参数</span>
              <h3>把边界定下来</h3>
            </div>
            <Database size={20} />
          </div>
          <p className="section-note">
            细节可以边聊边调整，生成前会再做一次硬件复核。
          </p>
          {gameRequirement && (
            <div className="recognized-game" role="status" aria-live="polite">
              <Gamepad2 size={16} aria-hidden="true" />
              <span>
                <span className="recognized-game-label">
                  已识别游戏：<strong>{gameRequirement.name}</strong>
                </span>
                <small>最低/推荐配置已载入</small>
              </span>
              <button
                type="button"
                onClick={() => setView("games")}
                aria-label={`查看${gameRequirement.name}配置`}
              >
                查看配置
                <ChevronRight size={14} aria-hidden="true" />
              </button>
            </div>
          )}
          <form
            className="needs-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleGenerate();
            }}
          >
            <div className="budget-field">
              <div className="budget-label-row">
                <span>预算范围</span>
                <span className="field-value">
                  ¥{formatMoney(profile.budget)}
                </span>
              </div>
              <input
                aria-label="预算"
                type="range"
                min={MIN_BUDGET}
                max={SLIDER_MAX_BUDGET}
                step="100"
                value={Math.min(profile.budget, SLIDER_MAX_BUDGET)}
                onChange={(event) =>
                  updateProfile("budget", normalizeBudget(Number(event.target.value)))
                }
              />
              <label className="budget-custom" htmlFor="budget-custom-input">
                <span>自定义预算</span>
                <span className="budget-number-wrap">
                  <span aria-hidden="true">¥</span>
                  <input
                    id="budget-custom-input"
                    aria-label="自定义预算"
                    aria-describedby="budget-custom-hint"
                    aria-invalid={budgetDraftHasError}
                    inputMode="numeric"
                    min={MIN_BUDGET}
                    max={MAX_CUSTOM_BUDGET}
                    step="1"
                    type="number"
                    value={budgetDraft}
                    onChange={(event) => setBudgetDraft(event.target.value)}
                    onBlur={commitBudgetDraft}
                  />
                </span>
              </label>
              <span
                className={`budget-custom-hint ${budgetDraftHasError ? "has-error" : ""}`}
                id="budget-custom-hint"
                role="status"
              >
                {budgetDraftValidation}
              </span>
              <span className="range-caption">
                <span>¥2,500</span>
                <span>¥20,000+</span>
              </span>
            </div>
            <label>
              主要用途
              <select
                value={profile.use_case}
                onChange={(event) =>
                  updateProfile("use_case", event.target.value)
                }
              >
                <option>游戏与日常</option>
                <option>视频剪辑与生产力</option>
                <option>直播与创作</option>
                <option>办公学习</option>
              </select>
            </label>
            <div className="field-grid">
              <label>
                目标分辨率
                <select
                  value={profile.resolution}
                  onChange={(event) =>
                    updateProfile("resolution", event.target.value)
                  }
                >
                  <option>1080P</option>
                  <option>2K</option>
                  <option>4K</option>
                </select>
              </label>
              <label>
                刷新率
                <select
                  value={profile.refresh_rate}
                  onChange={(event) =>
                    updateProfile("refresh_rate", Number(event.target.value))
                  }
                >
                  <option value="60">60Hz</option>
                  <option value="144">144Hz</option>
                  <option value="165">165Hz</option>
                  <option value="240">240Hz</option>
                </select>
              </label>
            </div>
            <fieldset>
              <legend>品牌偏好</legend>
              <div className="chip-grid">
                <button
                  type="button"
                  className={`choice-chip ${profile.cpu_brand === "amd" ? "selected" : ""}`}
                  onClick={() =>
                    updateProfile(
                      "cpu_brand",
                      profile.cpu_brand === "amd" ? "any" : "amd",
                    )
                  }
                >
                  AMD CPU
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.cpu_brand === "intel" ? "selected" : ""}`}
                  onClick={() =>
                    updateProfile(
                      "cpu_brand",
                      profile.cpu_brand === "intel" ? "any" : "intel",
                    )
                  }
                >
                  Intel CPU
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.gpu_brand === "nvidia" ? "selected" : ""}`}
                  onClick={() =>
                    updateProfile(
                      "gpu_brand",
                      profile.gpu_brand === "nvidia" ? "any" : "nvidia",
                    )
                  }
                >
                  NVIDIA 显卡
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.gpu_brand === "amd" ? "selected" : ""}`}
                  onClick={() =>
                    updateProfile(
                      "gpu_brand",
                      profile.gpu_brand === "amd" ? "any" : "amd",
                    )
                  }
                >
                  AMD 显卡
                </button>
              </div>
            </fieldset>
            <fieldset>
              <legend>散热方式</legend>
              <div className="cooling-choice">
                <button
                  type="button"
                  className={`cooling-option ${profile.cooling === "air" ? "selected" : ""}`}
                  onClick={() => updateProfile("cooling", "air")}
                >
                  <Thermometer size={17} />
                  风冷<span>安静、简单、好维护</span>
                </button>
                <button
                  type="button"
                  className={`cooling-option ${profile.cooling === "water" ? "selected" : ""}`}
                  onClick={() => updateProfile("cooling", "water")}
                >
                  <RefreshCw size={17} />
                  水冷<span>高性能、视觉更完整</span>
                </button>
              </div>
            </fieldset>
            <fieldset>
              <legend>机身大小</legend>
              <div className="chip-grid">
                <button
                  type="button"
                  className={`choice-chip ${profile.form_factor === "any" ? "selected" : ""}`}
                  onClick={() => updateProfile("form_factor", "any")}
                >
                  自动匹配
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.form_factor === "ATX" ? "selected" : ""}`}
                  onClick={() => updateProfile("form_factor", "ATX")}
                >
                  ATX
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.form_factor === "mATX" ? "selected" : ""}`}
                  onClick={() => updateProfile("form_factor", "mATX")}
                >
                  mATX
                </button>
                <button
                  type="button"
                  className={`choice-chip ${profile.form_factor === "Mini-ITX" ? "selected" : ""}`}
                  onClick={() => updateProfile("form_factor", "Mini-ITX")}
                >
                  ITX 小钢炮
                </button>
              </div>
            </fieldset>
            <button
              className="gold-button full-width"
              type="button"
              onClick={() => void handleGenerate()}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <RefreshCw size={17} className="spin" />
                  {jobMessage} {jobProgress}%
                </>
              ) : (
                <>
                  <Sparkles size={17} />
                   重新生成并核对
                  <ChevronRight size={17} />
                </>
              )}
            </button>
          </form>
          <div className="conversation-mini">
            <div className="mini-title">
              <MessageSquare size={15} />
              需求记录<span>{conversation?.messages.length ?? 1}</span>
            </div>
            <div className="mini-messages" aria-live="polite">
              {(conversation?.messages ?? localConversation(profile).messages)
                .slice(-3)
                .map((entry, index) => (
                  <div
                    className={`mini-message ${entry.role}`}
                    key={`${entry.created_at}-${index}`}
                  >
                    {entry.content}
                  </div>
                ))}
            </div>
          </div>
        </aside>
        <section className="plans-panel glass-card" id="plans-workbench">
          <div className="section-head plan-head">
            <div>
              <span className="eyebrow">02 / 方案工作台</span>
              <h3>找到适合你的那一套</h3>
            </div>
            <div className="plan-count">
              <Trophy size={16} />3 套参考方案
            </div>
          </div>
          {isGenerating && (
            <div className="job-progress" role="status" aria-live="polite">
              <div className="job-progress-head">
                <span>方案生成进度</span>
                <strong>{jobProgress}%</strong>
              </div>
              <div
                className="progress-track"
                aria-label={`方案生成进度 ${jobProgress}%`}
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={jobProgress}
              >
                <span style={{ width: `${jobProgress}%` }} />
              </div>
              <p>{jobMessage}，正在检查需求与兼容性…</p>
            </div>
          )}
          {!isGenerating && generationFeedback && (
            <div
              className={`generation-feedback ${
                generationFeedback.includes("失败") ||
                generationFeedback.includes("超时")
                  ? "has-error"
                  : ""
              }`}
              role="status"
              aria-live="polite"
            >
              {generationFeedback.includes("失败") ||
              generationFeedback.includes("超时") ? (
                <AlertTriangle size={16} aria-hidden="true" />
              ) : (
                <CheckCircle2 size={16} aria-hidden="true" />
              )}
              <span>{generationFeedback}</span>
            </div>
          )}
          <div className="plan-tabs" role="tablist" aria-label="方案类型">
            {plans.map((plan) => (
              <button
                key={plan.id}
                role="tab"
                aria-selected={plan.id === activePlanId}
                className={`plan-tab ${plan.id === activePlanId ? "active" : ""}`}
                onClick={() => setActivePlanId(plan.id)}
              >
                <span>{plan.title}</span>
                <small>
                  {plan.style === "value"
                    ? "轻预算"
                    : plan.style === "balanced"
                      ? "推荐"
                      : "高性能"}
                </small>
              </button>
            ))}
          </div>
          {activePlan && (
            <div className="plan-detail">
              <div className="plan-title-row">
                <div>
                  <h4>{activePlan.title}</h4>
                  <p>{activePlan.summary}</p>
                </div>
                <button
                  className="glass-button"
                  type="button"
                  onClick={handleExport}
                >
                  <Download size={16} />
                  导出清单
                </button>
              </div>
              <div className="metrics-grid">
                <div className="metric">
                  <CircleDollarSign size={18} />
                  <span>参考总价</span>
                  <strong>¥{formatMoney(activePlan.total_price)}</strong>
                </div>
                <div className="metric">
                  <Gauge size={18} />
                  <span>性能参考</span>
                  <strong>
                    {activePlan.performance_score}
                    <em>/ 100</em>
                  </strong>
                </div>
                <div className="metric">
                  <Zap size={18} />
                  <span>预计功耗</span>
                  <strong>
                    {activePlan.estimated_power_w}
                    <em>W</em>
                  </strong>
                </div>
              </div>
              {budgetIssue && (
                <div className="budget-alert" role="status" aria-live="polite">
                  <CircleDollarSign size={18} aria-hidden="true" />
                  <div>
                    <strong>{budgetIssue.title}</strong>
                    <p>{budgetIssue.detail}</p>
                  </div>
                </div>
              )}
              <div
                className={`compatibility-banner ${errors.length ? "has-error" : warnings.length ? "has-warning" : "is-ok"}`}
              >
                <div className="compat-icon">
                  {errors.length ? (
                    <X size={18} />
                  ) : warnings.length ? (
                    <RefreshCw size={18} />
                  ) : (
                    <CheckCircle2 size={18} />
                  )}
                </div>
                <div>
                  <strong>
                    {errors.length
                      ? `${errors.length} 项需要调整`
                      : warnings.length
                        ? `${warnings.length} 项建议关注`
                        : "配置通过兼容性检查"}
                  </strong>
                  <p>
                    {errors[0]?.detail ??
                      budgetIssue?.detail ??
                      warnings[0]?.detail ??
                      "插槽、尺寸、内存代际和电源余量均已检查。"}
                  </p>
                </div>
              </div>
              <CompatibilityChecklist issues={activePlan.compatibility} />
              <RecommendationCard
                recommendation={
                  recommendationPlanId === activePlan.id ? recommendation : null
                }
                plan={activePlan}
                profile={profile}
                loading={recommendationBusy && recommendationPlanId === activePlan.id}
                error={recommendationPlanId === activePlan.id ? recommendationError : ""}
                progress={recommendationProgress}
                message={recommendationMessage}
                onGenerate={() => void requestRecommendationForPlan(activePlan, profile)}
                onRegenerate={() => void requestRecommendationForPlan(activePlan, profile)}
                onOpenGame={() => setView("games")}
              />
              <div className="parts-list">
                {activePlan.items.map((item) => (
                  <div className="part-row" key={item.slot}>
                    <div className={`part-icon ${item.slot}`}>
                      <Cpu size={17} />
                    </div>
                    <button
                      className="part-main part-main-button"
                      type="button"
                      aria-label={`更换${SLOT_LABELS[item.slot]}：${item.part.name}`}
                      onClick={() => handleSwap(item)}
                    >
                      <span className="part-category">
                        {SLOT_LABELS[item.slot]}
                      </span>
                      <strong>{item.part.name}</strong>
                      <small>
                        {item.part.brand} · {item.part.source}
                      </small>
                    </button>
                    <div className="part-price">
                      ¥{formatMoney(item.part.price)}
                    </div>
                    <button
                      className="row-action"
                      type="button"
                      title={item.locked ? "解锁配置项" : "锁定配置项"}
                      aria-label={`${item.locked ? "解锁" : "锁定"}${SLOT_LABELS[item.slot]}`}
                      onClick={() => handleLock(item)}
                    >
                      {item.locked ? <Lock size={16} /> : <Unlock size={16} />}
                    </button>
                    <button
                      className="row-action swap"
                      type="button"
                      title="替换配置项"
                      aria-label={`替换${SLOT_LABELS[item.slot]}`}
                      onClick={() => handleSwap(item)}
                    >
                      换一件
                    </button>
                  </div>
                ))}
              </div>
              <div className="plan-footnote">
                <Check size={15} />
                所有价格为参考价，实际成交价以商品页面为准
              </div>
            </div>
          )}
        </section>
      </main>
      {renderPicker()}
    </>
  );

  const renderLadder = () => (
    <main className="page-view">
      <div className="page-title-row">
        <div>
          <span className="eyebrow">硬件性能参考</span>
          <h2>硬件天梯与手动选配</h2>
          <p>
            筛选型号并打开详情，可查看规格、排名、辅助点评和来源后再选入方案。
          </p>
        </div>
        <div className="view-tip">
          <BarChart3 size={17} />
          排行用于横向参考，兼容性由规则复核
        </div>
      </div>
      <div className="ladder-layout">
        <section className="ladder-card glass-card">
          <div className="toolbar">
            <div className="view-switch" role="tablist" aria-label="硬件类别">
              <button
                type="button"
                className={ladderCategory === "gpu" ? "selected" : ""}
                onClick={() => setLadderCategory("gpu")}
                role="tab"
                aria-selected={ladderCategory === "gpu"}
              >
                显卡天梯
              </button>
              <button
                type="button"
                className={ladderCategory === "cpu" ? "selected" : ""}
                onClick={() => setLadderCategory("cpu")}
                role="tab"
                aria-selected={ladderCategory === "cpu"}
              >
                CPU 天梯
              </button>
            </div>
            <span className="toolbar-meta">
              显示 {filteredLadder.length} / {ladderItems.length} 项
            </span>
          </div>
          <div className="ladder-filters">
            <label className="ladder-search">
              <Search size={16} />
              <input
                aria-label="搜索天梯型号"
                value={ladderQuery}
                onChange={(event) => setLadderQuery(event.target.value)}
                placeholder="搜索型号或特点"
              />
            </label>
            <label>
              <span>品牌</span>
              <select
                aria-label="筛选天梯品牌"
                value={ladderBrand}
                onChange={(event) => setLadderBrand(event.target.value)}
              >
                <option value="all">全部品牌</option>
                {ladderBrands.map((brand) => (
                  <option key={brand} value={brand}>
                    {brand}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>最低价</span>
              <input
                aria-label="天梯最低价格"
                inputMode="numeric"
                value={ladderMinPrice}
                onChange={(event) =>
                  setLadderMinPrice(event.target.value.replace(/\D/g, ""))
                }
                placeholder="不限"
              />
            </label>
            <label>
              <span>最高价</span>
              <input
                aria-label="天梯最高价格"
                inputMode="numeric"
                value={ladderMaxPrice}
                onChange={(event) =>
                  setLadderMaxPrice(event.target.value.replace(/\D/g, ""))
                }
                placeholder="不限"
              />
            </label>
          </div>
          <div className="ladder-list">
            {groupedLadder.map((group) => (
              <div className="tier-group" key={group.tier}>
                <div className={tierClass(group.tier)}>{group.tier} 档</div>
                <div className="tier-items">
                  {group.items.map((item) => (
                    <button
                      className="ladder-row"
                      type="button"
                      key={item.id}
                      onClick={() => openPartPicker(item.category, item.id)}
                    >
                      <span className="rank-number">
                        {String(item.rank).padStart(2, "0")}
                      </span>
                      <div className="ladder-name">
                        <strong>{item.name}</strong>
                        <small>
                          {item.brand} · {item.note}
                        </small>
                        <em>{item.source}</em>
                      </div>
                      <div className="score-track">
                        <span style={{ width: `${item.score}%` }} />
                        <em>{item.score}</em>
                      </div>
                      <div className="ladder-specs">
                        {item.vram_gb ? (
                          <span>{item.vram_gb}G 显存</span>
                        ) : null}
                        <span>{item.power_w}W</span>
                      </div>
                      <strong className="ladder-price">
                        ¥{formatMoney(item.reference_price ?? 0)}
                      </strong>
                      <ChevronRight className="ladder-open" size={16} />
                    </button>
                  ))}
                </div>
              </div>
            ))}
            {!groupedLadder.length && (
              <div className="ladder-empty">
                没有符合条件的型号，请调整筛选条件。
              </div>
            )}
          </div>
        </section>
        <aside className="side-guide glass-card">
          <div className="guide-icon">
            <Trophy size={20} />
          </div>
          <span className="eyebrow">操作流程</span>
          <h3>先筛选，再看详情。</h3>
          <p>
            点击任意型号可查看参数、排行、参考跑分、优缺点和来源；确认后可直接选入当前方案。
          </p>
          <div className="guide-line">
            <span>当前关注</span>
            <strong>{ladderCategory === "gpu" ? "显卡" : "CPU"}</strong>
          </div>
          <div className="guide-line">
            <span>关联方案</span>
            <strong>{activePlan?.title ?? "均衡耐用"}</strong>
          </div>
          <button
            className="glass-button full-width"
            type="button"
            onClick={() =>
              activePlan &&
              openPartPicker(
                ladderCategory,
                activePlan.items.find((item) => item.slot === ladderCategory)
                  ?.part.id,
              )
            }
          >
            <Sparkles size={16} />
            打开选配器
          </button>
        </aside>
      </div>
      {renderPicker()}
    </main>
  );

  const renderGames = () => (
    <main className="page-view">
      <div className="page-title-row">
        <div>
          <span className="eyebrow">Steam 配置参考</span>
          <h2>游戏能不能带得动？</h2>
          <p>查询游戏最低与推荐配置，再对照当前装机方案的方向做预算判断。</p>
        </div>
        <div className="view-tip">
          <Gamepad2 size={17} />
          最低配置不等于流畅体验
        </div>
      </div>
      <section className="game-search glass-card">
        <form onSubmit={handleGameSearch}>
          <label htmlFor="game-search-input">搜索游戏名称或 Steam App ID</label>
          <div className="query-row">
            <input
              id="game-search-input"
              aria-label="搜索游戏"
              value={gameQuery}
              onChange={(event) => setGameQuery(event.target.value)}
              placeholder="例如：War Thunder、warthuder 或 236390"
            />
            <button className="gold-button" type="submit" disabled={gameBusy}>
              {gameBusy ? (
                <RefreshCw size={17} className="spin" />
              ) : (
                <Search size={17} />
              )}
              查询
            </button>
          </div>
        </form>
        <div className="game-results" aria-label="游戏搜索结果">
          {gameResults.map((game) => (
            <button
              key={game.app_id}
              type="button"
              className={`game-result ${gameRequirement?.app_id === game.app_id ? "selected" : ""}`}
              onClick={() => selectGame(game)}
            >
              <Gamepad2 size={16} />
              <span>{game.name}</span>
              <small>App {game.app_id}</small>
              <ChevronRight size={15} />
            </button>
          ))}
          {!gameResults.length && (
            <div className="game-no-results">
              <Search size={17} />
              没有找到结果，请检查名称或尝试 Steam App ID。
            </div>
          )}
        </div>
      </section>
      {gameRequirement ? (
        <section className="game-detail glass-card">
          <div className="game-detail-head">
            <div>
              <span className="eyebrow">已选择游戏</span>
              <h3>{gameRequirement.name}</h3>
              <p>来源：{gameRequirement.source} · 字段缺失时显示“未提供”</p>
            </div>
            <button
              className="glass-button"
              type="button"
              onClick={() => setGameRequirement(null)}
            >
              <X size={16} />
              清除
            </button>
          </div>
          <div className="requirements-grid">
            <RequirementColumn
              title="最低配置"
              data={gameRequirement.minimum}
            />
            <RequirementColumn
              title="推荐配置"
              data={gameRequirement.recommended}
            />
          </div>
          <div className="game-note">
            <CheckCircle2 size={17} />
            <span>
              {gameRequirement.notes ||
                "建议结合目标分辨率、刷新率和实际画质设置判断。"}
            </span>
          </div>
        </section>
      ) : (
        <section className="empty-game glass-card">
          <Gamepad2 size={30} />
          <h3>选择一款游戏开始</h3>
          <p>
            默认提供可复现的本地快照；启用 Steam Provider
            后可补充官方商店公开字段。
          </p>
        </section>
      )}
    </main>
  );

  return (
    <div className={`app-shell theme-${theme}`} data-theme={theme}>
      <header className="topbar glass-nav">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Sparkles size={18} aria-hidden="true" />
          </div>
          <div>
            <p className="eyebrow">PC SETUP ASSISTANT</p>
            <h1>智能装机搭子</h1>
          </div>
        </div>
        <nav className="main-nav" aria-label="主导航">
          <button
            className={view === "builder" ? "active" : ""}
            onClick={() => {
              closePicker();
              setProductDetail(null);
              setView("builder");
            }}
          >
            <Cpu size={16} />
            配置方案
          </button>
          <button
            className={view === "ladder" ? "active" : ""}
            onClick={() => {
              closePicker();
              setProductDetail(null);
              setView("ladder");
            }}
          >
            <BarChart3 size={16} />
            硬件天梯
          </button>
          <button
            className={view === "games" ? "active" : ""}
            onClick={() => {
              closePicker();
              setProductDetail(null);
              setView("games");
            }}
          >
            <Gamepad2 size={16} />
            游戏配置
          </button>
        </nav>
        <div className="topbar-actions">
          <span className={`connection-pill ${demoMode ? "is-demo" : ""}`}>
            <span className="status-dot" />
            {demoMode ? "本地演示" : "API 已连接"}
          </span>
          <button
            className="icon-button"
            title="设置"
            aria-label="设置"
            onClick={() => setSettingsOpen((open) => !open)}
          >
            <Settings2 size={19} />
          </button>
          {settingsOpen && (
            <div
              className="settings-popover"
              role="dialog"
              aria-label="主题设置"
            >
              <div className="settings-title">
                <span>界面主题</span>
                <button
                  className="close-settings"
                  aria-label="关闭设置"
                  onClick={() => setSettingsOpen(false)}
                >
                  <X size={15} />
                </button>
              </div>
              <button
                className={`theme-option ${theme === "corporate" ? "selected" : ""}`}
                onClick={() => setTheme("corporate")}
              >
                <span className="theme-preview corporate-preview" />
                企业简洁风<small>默认</small>
              </button>
              <button
                className={`theme-option ${theme === "glass" ? "selected" : ""}`}
                onClick={() => setTheme("glass")}
              >
                <span className="theme-preview glass-preview" />
                玻璃拟态<small>夜色</small>
              </button>
              <button
                className={`theme-option ${theme === "neumorphism" ? "selected" : ""}`}
                onClick={() => setTheme("neumorphism")}
              >
                <span className="theme-preview neo-preview" />
                新拟物派<small>柔和</small>
              </button>
            </div>
          )}
        </div>
      </header>
      {productDetail ? (
        <ProductDetailPage
          detail={productDetail}
          busy={pickerBusy}
          onBack={() => setProductDetail(null)}
          onUse={handleUsePart}
        />
      ) : view === "builder" ? (
        renderBuilder()
      ) : view === "ladder" ? (
        renderLadder()
      ) : (
        renderGames()
      )}
      <footer className="statusbar">
        <div>
          <span className="status-dot" />
          {notice}
        </div>
        <span className="footer-meta">
          数据仅供选购参考 · 兼容性由规则引擎复核
        </span>
      </footer>
    </div>
  );
}
