export type BrandPreference = "any" | "amd" | "intel" | "nvidia";
export type CoolingPreference = "any" | "air" | "water";
export type PlanStyle = "value" | "balanced" | "performance";
export type PartCategory = "cpu" | "motherboard" | "gpu" | "memory" | "storage" | "psu" | "cooling" | "case";
export type LadderCategory = "cpu" | "gpu";
export type AppView = "builder" | "ladder" | "games";

export interface NeedProfile {
  budget: number;
  use_case: string;
  resolution: string;
  refresh_rate: number;
  cpu_brand: BrandPreference;
  gpu_brand: BrandPreference;
  cooling: CoolingPreference;
  aesthetics: string;
  noise: string;
  upgrade: string;
  existing_parts: string[];
}

export interface Part {
  id: string;
  category: PartCategory;
  name: string;
  brand: string;
  price: number;
  source: string;
  url?: string | null;
  image_url?: string | null;
  specs: Record<string, string | number>;
  power_w: number;
}

export interface CompatibilityIssue {
  code: string;
  severity: "error" | "warning";
  title: string;
  detail: string;
  related_slots: string[];
}

export interface BuildItem {
  slot: PartCategory;
  part: Part;
  locked: boolean;
  reason: string;
}

export interface BuildPlan {
  id: string;
  style: PlanStyle;
  title: string;
  summary: string;
  budget: number;
  total_price: number;
  estimated_power_w: number;
  performance_score: number;
  items: BuildItem[];
  compatibility: CompatibilityIssue[];
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  profile: NeedProfile;
  messages: { role: "assistant" | "user"; content: string; created_at: string }[];
}

export interface Job {
  id: string;
  kind: string;
  status: "queued" | "running" | "completed" | "cancelled" | "dead_letter";
  progress: number;
  message: string;
  result?: { plans?: BuildPlan[]; path?: string; file_name?: string; plan?: BuildPlan } | null;
  error?: string | null;
}

export interface HardwareLadderEntry {
  id: string;
  category: LadderCategory;
  tier: string;
  rank: number;
  name: string;
  brand: string;
  score: number;
  vram_gb?: number | null;
  power_w?: number | null;
  reference_price?: number | null;
  source: string;
  note: string;
}

export interface SystemRequirement {
  operating_system: string;
  processor: string;
  memory_gb?: number | null;
  graphics: string;
  directx?: string | null;
  storage_gb?: number | null;
  additional_notes?: string | null;
}

export interface GameSearchResult {
  app_id: string;
  name: string;
  source: string;
}

export interface GameRequirement {
  app_id: string;
  name: string;
  source: string;
  minimum: SystemRequirement;
  recommended: SystemRequirement;
  notes: string;
}
