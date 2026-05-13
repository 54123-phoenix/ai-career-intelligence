/** API client — typed wrappers around backend endpoints. */

import type { FinalT004Schema } from "@/types/simulation";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function runSimulation(params: {
  resume_id: string;
  job_id: string;
  strategy?: string;
}): Promise<FinalT004Schema> {
  const res = await fetch(`${BASE}/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: params.resume_id,
      job_id: params.job_id,
      strategy: params.strategy || "balanced",
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getSamples(): Promise<{
  resumes: Record<string, string>;
  jobs: Record<string, string>;
}> {
  const res = await fetch(`${BASE}/simulation/samples`);
  return res.json();
}
