export type BrandPreference = "any" | "amd" | "intel" | "nvidia";
export type CoolingPreference = "any" | "air" | "water";
export type PlanStyle = "value" | "balanced" | "performance";
export type PartCategory = "cpu" | "motherboard" | "gpu" | "memory" | "storage" | "psu" | "cooling" | "case";

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
