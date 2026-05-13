/** T010 API client — lightweight core layer endpoints */

import type { T010PipelineOutput } from '@/types/t010';
import { MOCK_PIPELINE_OUTPUT } from './mock-data';

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface T010RunRequest {
  user_id?: string;
  user_input: Record<string, unknown> | string;
  career_dataset?: Record<string, unknown>[] | null;
  industry_trends?: Record<string, unknown>[] | null;
  privacy_level?: string;
  previous_feedback?: Record<string, unknown> | null;
}

export interface T010RunResult {
  data: T010PipelineOutput;
  source: 'api' | 'mock';
}

export async function runT010Pipeline(params: T010RunRequest): Promise<T010RunResult> {
  try {
    const res = await fetch(`${BASE}/career/t010/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    return { data, source: 'api' };
  } catch (err) {
    // Fallback to mock data for demo/competition purposes
    console.warn('[T010] API unavailable, using mock data:', err);
    // Simulate network delay for realistic feel
    await new Promise((r) => setTimeout(r, 1800));
    return { data: MOCK_PIPELINE_OUTPUT, source: 'mock' };
  }
}

export async function getT010UpgradeInterfaces(): Promise<{
  version: string;
  description: string;
  agents: Record<
    string,
    {
      agent: string;
      core_capability: string;
      upgrade_hooks: string[];
      upgrade_notes: string;
      version: string;
    }
  >;
}> {
  const res = await fetch(`${BASE}/career/t010/upgrade-interfaces`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
