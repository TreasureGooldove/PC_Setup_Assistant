import type { BuildPlan, ConversationResponse, Job, NeedProfile, Part, PartCategory } from "./types";

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
