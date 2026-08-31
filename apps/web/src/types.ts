export type BrandPreference = "any" | "amd" | "intel" | "nvidia";
export type CoolingPreference = "any" | "air" | "water";
export type FormFactorPreference = "any" | "ATX" | "mATX" | "Mini-ITX";
export type PlanStyle = "value" | "balanced" | "performance";
export type PartCategory =
  | "cpu"
  | "motherboard"
  | "gpu"
  | "memory"
  | "storage"
  | "psu"
  | "cooling"
  | "case";
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
  form_factor: FormFactorPreference;
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
  specs: Record<string, unknown>;
  power_w: number;
  summary?: string;
  rank?: number | null;
  benchmark_score?: number | null;
  percentile?: number | null;
  advantages?: string[];
  cautions?: string[];
  data_updated_at?: string | null;
}

export interface CatalogFacetOption {
  value: string;
  label: string;
  count: number;
}

export interface CatalogFacets {
  brands: CatalogFacetOption[];
  kinds: CatalogFacetOption[];
  price_min: number;
  price_max: number;
}

export interface CatalogSyncStatus {
  enabled: boolean;
  status: "never" | "queued" | "running" | "completed" | "unavailable" | string;
  provider: string;
  item_count: number;
  message: string;
  updated_at?: string | null;
  stale: boolean;
  source_url?: string | null;
}

export interface CatalogResponse {
  items: Part[];
  total: number;
  facets: CatalogFacets;
  sync: CatalogSyncStatus;
}

export interface Offer {
  part_id: string;
  price: number;
  source: string;
  captured_at: string;
  platform: "jd" | "pdd" | "taobao" | string;
  sku?: string | null;
  list_price?: number | null;
  discount_price?: number | null;
  landed_price?: number | null;
  seller?: string | null;
  coupon_note?: string | null;
  status: string;
  url?: string | null;
  is_live: boolean;
}

export interface Evidence {
  source: string;
  title: string;
  url?: string | null;
  summary: string;
  confidence: string;
}

export interface DataSourceStatus {
  provider: string;
  kind: string;
  status:
    | "live"
    | "reference"
    | "fixture"
    | "disabled"
    | "unconfigured"
    | "unavailable"
    | string;
  note: string;
  url?: string | null;
  captured_at?: string | null;
}

export interface ProductDetail {
  part: Part;
  offers: Offer[];
  evidence: Evidence[];
  sources: DataSourceStatus[];
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
  messages: {
    role: "assistant" | "user";
    content: string;
    created_at: string;
  }[];
}

export interface Job {
  id: string;
  kind: string;
  status: "queued" | "running" | "completed" | "cancelled" | "dead_letter";
  progress: number;
  message: string;
  result?: {
    plans?: BuildPlan[];
    path?: string;
    file_name?: string;
    plan?: BuildPlan;
    category?: PartCategory;
    item_count?: number;
  } | null;
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
  source_url?: string | null;
  data_updated_at?: string | null;
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
