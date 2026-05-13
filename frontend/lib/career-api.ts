/** Career Analysis API — 职业分析引擎与职业模拟的业务语义封装
 *
 * 本层将底层 pipeline API（T008/T010 等构建产物）封装为业务语义函数，
 * 前端页面应直接调用此处函数，而非直接引用 t008-api / t010-api。
 */

import type { T010PipelineOutput } from "@/types/t010";
import type { T008PipelineOutput } from "@/types/t008";
import { runT010Pipeline } from "./t010-api";
import { runT008Pipeline } from "./t008-api";

export interface CareerAnalysisRequest {
  user_id?: string;
  user_input: string;
  career_dataset?: Record<string, unknown>[];
  privacy_level?: string;
}

export interface CareerAnalysisResult {
  data: T010PipelineOutput;
  source: "api" | "mock";
}

/** 职业综合分析 — 解析画像、推荐岗位、生成策略、模拟验证 */
export async function analyzeCareer(
  params: CareerAnalysisRequest
): Promise<CareerAnalysisResult> {
  return runT010Pipeline({
    user_id: params.user_id,
    user_input: params.user_input,
    career_dataset: params.career_dataset,
    privacy_level: params.privacy_level,
  });
}

/** 职业推荐与策略对比 — 返回结构化推荐列表与策略评分 */
export async function getCareerRecommendations(
  params: CareerAnalysisRequest
): Promise<T008PipelineOutput> {
  return runT008Pipeline({
    user_id: params.user_id,
    user_input: params.user_input,
    career_dataset: params.career_dataset,
  });
}

/** 提交用户反馈 — 用于优化后续职业推荐与策略 */
export async function submitCareerFeedback(params: {
  user_id: string;
  strategy_adopted?: string | null;
  strategy_rating?: number;
  comments?: string;
}): Promise<{ received: boolean; feedback_id: string }> {
  const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const res = await fetch(`${BASE}/career/feedback`, {
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
