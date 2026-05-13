/** @deprecated — 本文件保留向后兼容，新代码请使用 lib/api/career.ts */

import type { T010PipelineOutput } from '@/types/t010';
import { runT010Pipeline } from './t010-api';

export interface CareerAnalysisRequest {
  user_id?: string;
  user_input: string;
  career_dataset?: Record<string, unknown>[];
  privacy_level?: string;
}

export interface CareerAnalysisResult {
  data: T010PipelineOutput;
  source: 'api' | 'mock';
}

export async function analyzeCareer(params: CareerAnalysisRequest): Promise<CareerAnalysisResult> {
  return runT010Pipeline({
    user_id: params.user_id,
    user_input: params.user_input,
    career_dataset: params.career_dataset,
    privacy_level: params.privacy_level,
  });
}

export async function submitCareerFeedback(params: {
  user_id: string;
  strategy_adopted?: string | null;
  strategy_rating?: number;
  comments?: string;
}): Promise<{ received: boolean; feedback_id: string }> {
  const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const res = await fetch(`${BASE}/career/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
