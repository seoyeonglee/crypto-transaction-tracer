import type { Direction, MetaResponse, TraceResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,

  meta() {
    return request<MetaResponse>("/api/v1/meta");
  },

  trace(seed: string, hops: number, direction: Direction) {
    const query = new URLSearchParams({
      seed,
      max_hops: String(hops),
      direction,
    });
    return request<TraceResponse>(`/api/v1/trace?${query.toString()}`);
  },
};
