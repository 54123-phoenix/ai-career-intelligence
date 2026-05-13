/** T009 API client — typed wrappers around /api/v1/career/t009 endpoints */

import type { T009PipelineOutput } from "@/types/t009";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface T009RunRequest {
  user_id?: string;
  user_input: Record<string, unknown> | string;
  career_dataset?: Record<string, unknown>[] | null;
  industry_trends?: Record<string, unknown>[] | null;
  privacy_level?: string;
  previous_feedback?: Record<string, unknown> | null;
}

export async function runT009Pipeline(
  params: T009RunRequest,
): Promise<T009PipelineOutput> {
  const res = await fetch(`${BASE}/career/t009/run`, {
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

export interface T009FeedbackRequest {
  user_id: string;
  session_id?: string;
  strategy_adopted?: string | null;
  strategy_rating?: number;
  nodes_clicked?: string[];
  time_spent_sections?: Record<string, number>;
  comments?: string;
  preferences_updated?: Record<string, unknown>;
  privacy_level?: string;
}

export async function submitT009Feedback(
  params: T009FeedbackRequest,
): Promise<{ received: boolean; feedback_id: string; feedback_loop: Record<string, unknown> }> {
  const res = await fetch(`${BASE}/career/t009/feedback`, {
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

export async function listT009Baselines(): Promise<{
  count: number;
  templates: Record<string, unknown>[];
}> {
  const res = await fetch(`${BASE}/career/t009/baselines`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function analyzeT009Trends(params: T009RunRequest) {
  const res = await fetch(`${BASE}/career/t009/trends`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
