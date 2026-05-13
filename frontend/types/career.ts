/** Career Domain Types — 职业分析与模拟的业务类型定义
 *
 * 本文件定义业务语义类型，与 T00x 解耦。
 * 不直接 import types/t008.ts 或 types/t010.ts。
 */

export interface UserProfileSummary {
  id: string;
  name?: string;
  email?: string;
  experienceYears: number;
  educationLevel: string;
  skills: string[];
  careerGoals: string[];
  preferredLocations: string[];
}

export interface JobRecommendation {
  id: string;
  title: string;
  company: string;
  location: string;
  matchScore: number;
  requiredSkills: string[];
  salaryRange?: [number, number] | null;
}

export interface CareerStrategy {
  id: string;
  name: string;
  description: string;
  overallScore: number;
  dimensions: Record<string, number>;
  isOffPath: boolean;
}

export interface CareerPlan {
  steps: unknown[];
}

export interface SimulationSummary {
  id: string;
  strategyName: string;
  outcome: string;
  successProbability: number;
  timeline: unknown[];
  skillGap: unknown[];
  recommendations: string[];
  confidenceScore: {
    overall: number;
    factors: Record<string, number>;
  };
}

export interface CareerAnalysisResult {
  id: string;
  status: 'success' | 'partial' | 'failed';
  userProfile?: UserProfileSummary;
  recommendations: JobRecommendation[];
  strategies: CareerStrategy[];
  plan?: CareerPlan;
  simulationResult?: SimulationSummary;
  generatedAt: string;

  // Extended fields for transitional UI compatibility
  // These map to legacy T010 fields and will be refactored in future phases
  frontendData?: {
    summary?: {
      headline?: string;
      topStrategyScore?: number;
      simulationSuccessRate?: number;
    };
    strategyComparison?: unknown;
    actionTimeline?: unknown[];
    recommendationsList?: unknown[];
  };
  careerData?: {
    totalEntries: number;
    entries: Array<{
      jobTitle: string;
      requiredSkills: string[];
    }>;
  };
}
