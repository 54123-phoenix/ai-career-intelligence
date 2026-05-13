/** T008 API client — typed wrappers around /api/v1/career/t008 endpoints */

import type { T008PipelineOutput } from "@/types/t008";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface T008RunRequest {
  user_id?: string;
  user_input: Record<string, unknown> | string;
  career_dataset?: Record<string, unknown>[] | null;
}

export async function runT008Pipeline(
  params: T008RunRequest,
): Promise<T008PipelineOutput> {
  const res = await fetch(`${BASE}/career/t008/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function t008Parse(params: T008RunRequest) {
  const res = await fetch(`${BASE}/career/t008/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function t008Retrieve(params: T008RunRequest) {
  const res = await fetch(`${BASE}/career/t008/retrieve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function t008Review(params: T008RunRequest) {
  const res = await fetch(`${BASE}/career/t008/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function t008Architect(params: T008RunRequest) {
  const res = await fetch(`${BASE}/career/t008/architect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function t008Simulate(params: T008RunRequest) {
  const res = await fetch(`${BASE}/career/t008/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function t008Frontend(userId: string) {
  const res = await fetch(`${BASE}/career/t008/frontend/${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
