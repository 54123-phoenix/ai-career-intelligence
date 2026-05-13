/** Career Analysis API — 职业分析引擎业务语义封装
 *
 * 本层将底层 pipeline API 封装为业务函数。
 * 前端页面应直接调用此处函数。
 */

import { apiFetch } from './client';
import type {
  CareerAnalysisResult,
  JobRecommendation,
  CareerStrategy,
} from '@/types/career';
import type { CareerPathGraph } from '@/types/simulation';

export interface AnalyzeCareerRequest {
  user_input: string;
  user_id?: string;
  career_dataset?: Record<string, unknown>[];
  privacy_level?: string;
  resume_data?: Record<string, unknown>;
  depth?: 'quick' | 'standard' | 'deep';
}

export interface AnalyzeCareerResponse {
  data: CareerAnalysisResult;
  source: 'api' | 'mock';
}

/** 职业综合分析 — 解析画像、推荐岗位、生成策略、模拟验证 */
export async function analyzeCareer(
  params: AnalyzeCareerRequest
): Promise<AnalyzeCareerResponse> {
  try {
    const raw = await apiFetch<Record<string, unknown>>('/career/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    });
    return { data: adaptApiToCareerResult(raw), source: 'api' };
  } catch {
    // Fallback：若后端 facade 未就绪，降级到 T010（内部兼容，不暴露给上层）
    const { runT010Pipeline } = await import('@/lib/t010-api');
    const result = await runT010Pipeline({
      user_id: params.user_id || 'demo-user',
      user_input: params.user_input,
      career_dataset: params.career_dataset,
      privacy_level: params.privacy_level || 'basic',
    });
    // 将 T010 输出转换为业务类型（适配层）
    return {
      data: adaptT010ToCareerResult(result.data),
      source: 'mock',
    };
  }
}

/** 获取岗位推荐列表 */
export async function getJobRecommendations(): Promise<JobRecommendation[]> {
  return apiFetch<JobRecommendation[]>('/career/recommendations');
}

/** 获取匹配评分 */
export async function getMatchScore(params: {
  resume_id: string;
  job_id: string;
}): Promise<{ score: number; breakdown: Record<string, number> }> {
  const search = new URLSearchParams();
  search.set('resume_id', params.resume_id);
  search.set('job_id', params.job_id);
  return apiFetch(`/career/match-score?${search.toString()}`);
}

/** 上传简历 */
export async function uploadResume(file: File): Promise<{
  resume_id: string;
  parsed: Record<string, unknown>;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const token = typeof window !== 'undefined' ? localStorage.getItem('aci_token') : null;

  const res = await fetch(`${BASE}/career/resume`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

/** 提交用户反馈 */
export async function submitCareerFeedback(params: {
  analysis_id: string;
  rating: number;
  comments?: string;
  adopted_strategy?: string;
}): Promise<{ received: boolean }> {
  return apiFetch('/career/feedback', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/** 获取职业路径图数据 */
export async function getCareerPath(): Promise<CareerPathGraph> {
  return apiFetch<CareerPathGraph>('/career/path');
}

/** 获取长期趋势 */
export async function getCareerTrends(): Promise<{
  trends: Array<{
    domain: string;
    trend_name: string;
    direction: string;
    growth_rate_pct: number;
  }>;
}> {
  return apiFetch('/career/trends');
}

// ── Internal adapters ───────────────────────────────────────────────────

/** Backend facade (/career/analyze) → CareerAnalysisResult */
function adaptApiToCareerResult(api: Record<string, unknown>): CareerAnalysisResult {
  // 后端 facade 返回的结构与 T010 输出一致（snake_case 字段名）
  // 复用 T010 adapter 做统一转换
  return adaptT010ToCareerResult({
    execution_id: api.id,
    status: api.status,
    user_profile: api.user_profile,
    job_recommendations: api.recommendations,
    strategy_list: api.strategies,
    career_plan: api.plan,
    simulation_feedback: api.simulation,
    frontend_data: api.frontend_data,
    generated_at: api.generated_at,
    career_data: api.career_data,
    errors: api.errors || [],
  });
}

function adaptT010ToCareerResult(t010: unknown): CareerAnalysisResult {
  const data = t010 as Record<string, unknown>;
  const fd = (data.frontend_data as Record<string, unknown>) || {};
  const summary = (fd.summary as Record<string, unknown>) || {};
  const userProfile = data.user_profile as Record<string, unknown> | null;

  return {
    id: String(data.execution_id || 'unknown'),
    status: (data.status as 'success' | 'partial' | 'failed') || 'partial',
    userProfile: userProfile
      ? {
          id: String(userProfile.user_id || ''),
          name: '',
          email: '',
          experienceYears: Number(userProfile.experience_years || 0),
          educationLevel: String(userProfile.education_level || ''),
          skills: (userProfile.skills as string[]) || [],
          careerGoals: (userProfile.career_goals as string[]) || [],
          preferredLocations: (userProfile.preferred_locations as string[]) || [],
        }
      : undefined,
    recommendations: ((data.job_recommendations as unknown[]) || []).map((j: any) => ({
      id: j.job_id || j.title,
      title: j.title || '',
      company: j.company || '',
      location: j.location || '',
      matchScore: j.match_score || 0,
      requiredSkills: j.required_skills || [],
      salaryRange: j.salary_range || null,
    })),
    strategies: ((data.strategy_list as unknown[]) || []).map((s: any, i: number) => ({
      id: s.strategy?.strategy_id || `strat-${i}`,
      name: s.strategy?.strategy_name || '',
      description: s.strategy?.description || '',
      overallScore: s.overall_score || 0,
      dimensions: s.scores || {},
      isOffPath: s.off_path || false,
    })),
    plan: data.career_plan
      ? {
          steps: ((data.career_plan as Record<string, unknown>).steps as unknown[]) || [],
        }
      : undefined,
    simulationResult: data.simulation_feedback
      ? {
          id: 'sim-' + String(data.execution_id || ''),
          strategyName: '',
          outcome: 'timeout',
          successProbability:
            ((data.simulation_feedback as Record<string, unknown>).base_feedback as Record<string, unknown>)?.average_success_rate as number || 0,
          timeline: [],
          skillGap: [],
          recommendations: [],
          confidenceScore: { overall: 0, factors: {} },
        }
      : undefined,
    generatedAt: String(data.generated_at || new Date().toISOString()),
    frontendData: {
      summary: {
        headline: String(summary.headline || ''),
        topStrategyScore: Number(summary.top_strategy_score || 0),
        simulationSuccessRate: Number(summary.simulation_success_rate || 0),
      },
      strategyComparison: fd.strategy_comparison,
      actionTimeline: (fd.action_timeline as unknown[]) || [],
      recommendationsList: (fd.recommendations as unknown[]) || [],
    },
    careerData: data.career_data
      ? {
          totalEntries: Number((data.career_data as Record<string, unknown>).total_entries || 0),
          entries: ((data.career_data as Record<string, unknown>).entries as Array<Record<string, unknown>> || []).map((e) => ({
            jobTitle: String(e.job_title || ''),
            requiredSkills: (e.required_skills as string[]) || [],
          })),
        }
      : undefined,
  };
}
