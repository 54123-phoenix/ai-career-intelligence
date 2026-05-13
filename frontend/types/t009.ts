/** T009 TypeScript types — aligned with backend/career/t009_schemas.py */

import type {
  UserProfile,
  CareerData,
  CareerDataEntry,
  JobRecommendation,
  StrategyCandidate,
  CareerPlan,
  PlanStep,
  SkillNode,
  TimelineNode,
  VisualizationGraph,
  SimulationRound,
  SimulationFeedback,
  ActionTimelineEntry,
  StrategyComparisonData,
  FrontendSummary,
} from './t008';

// ── T009 Parser Output ────────────────────────────────────────────────────

export interface BaselineStrategyTemplate {
  template_id: string;
  domain: string;
  target_role: string;
  typical_skills: string[];
  typical_timeline_months: number;
  typical_milestones: string[];
  recommended_strategies: string[];
  risk_factors: string[];
  source: string;
}

export interface BaselineStrategy {
  baseline_id: string;
  templates: BaselineStrategyTemplate[];
  matched_template_id: string | null;
  match_confidence: number;
  generated_at: string;
}

export interface OffPathFlag {
  strategy_id: string;
  flag_type:
    | 'skill_order_anomaly'
    | 'timeline_deviation'
    | 'role_skip'
    | 'industry_jump'
    | 'salary_mismatch';
  severity: 'low' | 'medium' | 'high';
  description: string;
  deviation_score: number;
  recommendation: string;
}

// ── T009 Reviewer Output ──────────────────────────────────────────────────

export interface DiversityMetric {
  strategy_diversity: number;
  dimension_balance: Record<string, number>;
  overfitting_risk: number;
  recommendation: string;
}

export interface DynamicWeights {
  iteration: number;
  weights: Record<string, number>;
  weight_history: Record<string, number>[];
  convergence_delta: number;
  learning_rate: number;
}

export interface ScoredStrategyV2 {
  strategy: StrategyCandidate;
  scores: Record<string, number>;
  overall_score: number;
  rationale: string;
  rank: number;
  off_path: boolean;
  off_path_flags: OffPathFlag[];
}

// ── T009 Architect Output ─────────────────────────────────────────────────

export interface IndustryTrend {
  trend_id: string;
  domain: string;
  trend_name: string;
  direction: 'rising' | 'stable' | 'declining';
  confidence: number;
  affected_skills: string[];
  affected_roles: string[];
  growth_rate_pct: number;
  source: string;
  valid_until: string;
}

export interface TrendReport {
  report_id: string;
  domain: string;
  trends: IndustryTrend[];
  generated_at: string;
  summary: string;
}

// ── Privacy ───────────────────────────────────────────────────────────────

export interface PrivacyMask {
  mask_personal_info: boolean;
  mask_company_names: boolean;
  mask_salary: boolean;
  anonymization_level: 'none' | 'basic' | 'full';
  masked_fields: string[];
}

// ── Feedback Loop ─────────────────────────────────────────────────────────

export interface FeedbackLoopState {
  state_id: string;
  retrieval_reviewer_iterations: number;
  reviewer_weight_updates: number;
  simulation_feedback_applied: boolean;
  simulation_rounds_run: number;
  user_feedback_received: boolean;
  user_strategy_adopted: string | null;
  user_behavior_preferences: Record<string, unknown>;
  pipeline_converged: boolean;
  convergence_reason: string;
}

export interface UserFeedback {
  feedback_id: string;
  user_id: string;
  session_id: string;
  timestamp: string;
  strategy_adopted: string | null;
  strategy_rating: number;
  nodes_clicked: string[];
  time_spent_sections: Record<string, number>;
  comments: string;
  preferences_updated: Record<string, unknown>;
  privacy_level: 'none' | 'basic' | 'full';
}

// ── T009 Simulation Output ────────────────────────────────────────────────

export interface T009SimulationFeedback {
  base_feedback: SimulationFeedback;
  weight_updates_applied: number;
  updated_weights: DynamicWeights | null;
  off_path_strategies_detected: string[];
  rl_iteration: number;
  rl_converged: boolean;
}

// ── T009 Unified Output ───────────────────────────────────────────────────

export interface T009PipelineOutput {
  execution_id: string;
  status: 'success' | 'partial' | 'failed';
  errors: string[];

  // Stage 1
  user_profile: UserProfile | null;
  career_data: CareerData | null;
  baseline_strategy: BaselineStrategy | null;
  off_path_flags: OffPathFlag[];
  new_user_generated: boolean;

  // Stage 2
  job_recommendations: JobRecommendation[];
  strategy_candidates: StrategyCandidate[];

  // Stage 3
  strategy_list: ScoredStrategyV2[];
  diversity_metric: DiversityMetric | null;
  dynamic_weights: DynamicWeights | null;

  // Stage 4
  career_plan: CareerPlan | null;
  visualization_data: VisualizationGraph | null;
  trend_adjustments: string[];
  interactive_nodes: Record<string, Record<string, unknown>>;
  long_term_outlook: string;

  // Stage 5
  simulation_feedback: T009SimulationFeedback | null;
  refined_strategy_list: ScoredStrategyV2[] | null;

  // Stage 6
  frontend_data: Record<string, unknown>;
  privacy_mask: PrivacyMask | null;

  // Feedback
  feedback_loop: FeedbackLoopState | null;
  user_feedback: UserFeedback | null;

  // Meta
  elapsed_ms: number;
  generated_at: string;
  t009_version: string;
}
