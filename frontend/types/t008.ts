/** T008 TypeScript types — aligned with backend/career/t008_schemas.py */

// ── Parser Agent Output ──────────────────────────────────────────────────

export interface UserProfile {
  user_id: string;
  career_goals: string[];
  skills: string[];
  experience_years: number;
  education_level: string;
  preferred_locations: string[];
  preferred_industries: string[];
  salary_expectation: [number, number] | null;
  raw_text: string;
}

export interface CareerDataEntry {
  job_title: string;
  required_skills: string[];
  optional_skills: string[];
  growth_path: string[];
  level: string;
  salary_range: [number, number] | null;
  location: string;
  industry: string;
  source: string;
}

export interface CareerData {
  dataset_id: string;
  entries: CareerDataEntry[];
  total_entries: number;
  processed_at: string;
}

export interface ParserOutput {
  user_profile: UserProfile;
  career_data: CareerData | null;
  warnings: string[];
}

// ── Retrieval Agent Output ────────────────────────────────────────────────

export interface JobRecommendation {
  job_id: string;
  title: string;
  company: string;
  location: string;
  level: string;
  required_skills: string[];
  optional_skills: string[];
  salary_range: [number, number] | null;
  match_score: number;
  match_details: Record<string, unknown>;
}

export interface StrategyCandidate {
  strategy_id: string;
  strategy_name: string;
  description: string;
  match_score: number;
  historical_success_rate: number;
  source: string;
}

export interface RetrievalOutput {
  job_recommendations: JobRecommendation[];
  strategy_candidates: StrategyCandidate[];
  total_matches: number;
}

// ── Reviewer Agent Output ─────────────────────────────────────────────────

export interface ScoredStrategy {
  strategy: StrategyCandidate;
  scores: {
    success_rate: number;
    match_degree: number;
    growth_cycle: number;
    skill_adaptability: number;
  };
  overall_score: number;
  rationale: string;
  rank: number;
}

export interface ReviewerOutput {
  strategy_list: ScoredStrategy[];
  top_n: number;
  scoring_weights: Record<string, number>;
}

// ── Architect Agent Output ────────────────────────────────────────────────

export type PlanPhase = 'preparation' | 'application' | 'interview' | 'negotiation' | 'onboarding';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type TimelineEventType =
  | 'skill_acquisition'
  | 'application'
  | 'interview'
  | 'offer'
  | 'milestone';

export interface PlanStep {
  step_number: number;
  phase: PlanPhase;
  title: string;
  description: string;
  duration_days: number;
  skills_required: string[];
  skills_acquired: string[];
  milestones: string[];
}

export interface SkillNode {
  skill_name: string;
  level: SkillLevel;
  dependencies: string[];
  estimated_hours: number;
}

export interface TimelineNode {
  week: number;
  label: string;
  event_type: TimelineEventType;
  details: string;
}

export interface CareerPlan {
  plan_id: string;
  user_id: string;
  generated_at: string;
  selected_strategy: ScoredStrategy | null;
  alternative_strategies: ScoredStrategy[];
  steps: PlanStep[];
  total_duration_days: number;
  estimated_success_rate: number;
  risk_points: string[];
  skill_gaps: string[];
  recommendation: string;
}

export interface VisualizationGraph {
  skill_nodes: SkillNode[];
  skill_edges: [string, string][];
  timeline_nodes: TimelineNode[];
  primary_path: string[];
  alternative_paths: string[][];
  strategy_comparison: Record<
    string,
    {
      success_rate: number;
      growth_cycle: number;
      skill_adaptability: number;
    }
  >;
  render_hints: Record<string, unknown>;
}

export interface ArchitectOutput {
  career_plan: CareerPlan;
  visualization_data: VisualizationGraph;
}

// ── Simulation Agent Output ───────────────────────────────────────────────

export interface SimulationRound {
  round_id: number;
  success: boolean;
  success_probability: number;
  risk_triggered: string[];
  skill_gaps_exposed: string[];
  steps_to_outcome: number;
  notes: string;
}

export interface SimulationFeedback {
  simulation_id: string;
  career_plan_id: string;
  total_rounds: number;
  successful_rounds: number;
  average_success_rate: number;
  rounds: SimulationRound[];
  aggregated_risks: Record<string, number>;
  aggregated_skill_gaps: Record<string, number>;
  recommendation: string;
}

// ── T008 Pipeline Output ──────────────────────────────────────────────────

export interface T008PipelineOutput {
  execution_id: string;
  status: 'success' | 'partial' | 'failed';
  errors: string[];
  user_profile: UserProfile | null;
  career_data: CareerData | null;
  job_recommendations: JobRecommendation[];
  strategy_candidates: StrategyCandidate[];
  strategy_list: ScoredStrategy[];
  career_plan: CareerPlan | null;
  visualization_data: VisualizationGraph | null;
  simulation_feedback: SimulationFeedback | null;
  refined_strategy_list: ScoredStrategy[] | null;
  frontend_data: FrontendData;
  elapsed_ms: number;
  generated_at: string;
}

// ── Frontend-ready data ───────────────────────────────────────────────────

export interface FrontendData {
  summary: FrontendSummary;
  career_path_graph: VisualizationGraph;
  strategy_comparison: StrategyComparisonData;
  action_timeline: ActionTimelineEntry[];
  simulation_chart: SimulationChartData;
  recommendations: RecommendationItem[];
}

export interface FrontendSummary {
  headline: string;
  user_skills: string[];
  career_goals: string[];
  total_jobs_matched: number;
  top_strategy_score: number;
  simulation_success_rate: number;
  simulation_rounds: number;
}

export interface StrategyComparisonData {
  strategies: StrategyComparisonEntry[];
  dimensions: string[];
}

export interface StrategyComparisonEntry {
  name: string;
  overall: number;
  success_rate: number;
  match_degree: number;
  growth_cycle: number;
  skill_adaptability: number;
  rank: number;
}

export interface ActionTimelineEntry {
  step_number: number;
  phase: string;
  title: string;
  description: string;
  start_day: number;
  end_day: number;
  duration_days: number;
  milestones: string[];
}

export interface SimulationChartData {
  rounds: SimulationChartRound[];
  average: number;
  successful: number;
  total: number;
  top_risks: Record<string, number>;
  top_gaps: Record<string, number>;
}

export interface SimulationChartRound {
  round: number;
  probability: number;
  success: boolean;
}

export interface RecommendationItem {
  priority: number;
  type: string;
  title: string;
  description: string;
}
