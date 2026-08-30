import type { BuildPlan, ConversationResponse, GameRequirement, GameSearchResult, HardwareLadderEntry, Job, NeedProfile, Part, PartCategory, LadderCategory } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: { message?: string } } | null;
    throw new ApiError(response.status, body?.error?.message ?? `请求失败（${response.status}）`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  createConversation: (profile: NeedProfile) => request<ConversationResponse>("/api/conversations", { method: "POST", body: JSON.stringify({ profile }) }),
  updateProfile: (id: string, profile: NeedProfile) => request<ConversationResponse>(`/api/conversations/${id}/profile`, { method: "PATCH", body: JSON.stringify({ profile }) }),
  sendMessage: (id: string, content: string) => request<ConversationResponse>(`/api/conversations/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  generate: (conversationId: string) => request<Job>(`/api/plans/generate?conversation_id=${encodeURIComponent(conversationId)}`, { method: "POST", headers: { "Idempotency-Key": `generate:${conversationId}:${Date.now()}` } }),
  getJob: (id: string) => request<Job>(`/api/jobs/${id}`),
  getPlans: (conversationId: string) => request<{ plans: BuildPlan[] }>(`/api/plans?conversation_id=${encodeURIComponent(conversationId)}`),
  getCatalog: (category: PartCategory) => request<{ items: Part[] }>(`/api/catalog/${category}`),
  getLadder: (category: LadderCategory, filters: { query?: string; brand?: string; minPrice?: number; maxPrice?: number } = {}) => {
    const params = new URLSearchParams({ category });
    if (filters.query) params.set("query", filters.query);
    if (filters.brand) params.set("brand", filters.brand);
    if (filters.minPrice !== undefined) params.set("min_price", String(filters.minPrice));
    if (filters.maxPrice !== undefined) params.set("max_price", String(filters.maxPrice));
    return request<{ items: HardwareLadderEntry[] }>(`/api/ladder?${params.toString()}`);
  },
  searchGames: (query: string) => request<{ items: GameSearchResult[] }>(`/api/games/search?query=${encodeURIComponent(query)}`),
  getGameRequirements: (appId: string) => request<GameRequirement>(`/api/games/${encodeURIComponent(appId)}/requirements`),
  replaceItem: (planId: string, slot: PartCategory, partId: string, locked: boolean) => request<BuildPlan>(`/api/plans/${planId}/items/${slot}`, { method: "PATCH", body: JSON.stringify({ part_id: partId, locked }) }),
  exportPlan: (planId: string) => request<Job>(`/api/plans/${planId}/exports`, { method: "POST", headers: { "Idempotency-Key": `export:${planId}:${Date.now()}` } }),
};

export function streamJob(id: string, onEvent: (event: { progress: number; message: string; status: string }) => void, onDone: () => void): () => void {
  const source = new EventSource(`${API_BASE}/api/jobs/${id}/events`);
  source.addEventListener("job", (raw) => {
    const data = JSON.parse((raw as MessageEvent).data) as { progress: number; message: string; status: string };
    onEvent(data);
    if (["completed", "cancelled", "dead_letter"].includes(data.status)) {
      source.close();
      onDone();
    }
  });
  source.onerror = () => source.close();
  return () => source.close();
}
