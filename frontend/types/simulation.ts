/** FinalT004Schema — unified simulation response consumed by the Dashboard. */

export interface FinalT004Schema {
  simulation_id: string;
  strategy_name: string;
  outcome: "accepted" | "rejected" | "timeout";

  // ProductView (UI rendering)
  summary: SummarySection;
  match_score: MatchScoreSection;
  timeline: TimelineSection;
  skill_gap_chart: SkillGapChartSection;
  recommendation_cards: RecommendationCard[];

  // Explanation (interpretability)
  decision_path: DecisionPath;
  hr_reasoning: HRReasoning;
  candidate_actions: CandidateActions;
  failure_points: FailurePoint[];
  confidence_score: ConfidenceScore;

  // Raw data
  result: Record<string, unknown>;
  metrics: Record<string, number>;
}

// ── ProductView sections ──────────────────────────────────────────────

export interface SummarySection {
  headline: string;
  candidate_name: string;
  job_title: string;
  company: string;
  badge: "success" | "failure" | "warning";
  stats: {
    success_probability: number;
    time_to_offer_steps: number;
    total_reward: number;
  };
}

export interface MatchScoreSection {
  overall: number;
  breakdown: {
    skill_match: number;
    experience_fit: number;
    keyword_overlap: number;
  };
  gauge: {
    value: number;
    color: "green" | "yellow" | "red";
    label: string;
  };
}

export interface TimelineSection {
  events: TimelineEvent[];
  total_steps: number;
}

export interface TimelineEvent {
  step: number;
  phase: "applied" | "screened" | "interview" | "offer" | "accepted" | "rejected";
  actor: "candidate" | "hr" | "interview" | "system";
  action_label: string;
  reasoning: string;
  score?: number;
  confidence?: number;
  timestamp: string;
}

export interface SkillGapChartSection {
  matched: SkillBar[];
  missing: SkillBar[];
  title: string;
  match_ratio: number;
}

export interface SkillBar {
  name: string;
  value: number;
  category: "required" | "optional" | "bonus";
}

export interface RecommendationCard {
  priority: number;
  type: "action" | "warning" | "info" | "success";
  title: string;
  description: string;
  action_label?: string;
}

// ── Explanation sections ──────────────────────────────────────────────

export interface DecisionPath {
  title: string;
  total_actions: number;
  steps: DecisionStep[];
}

export interface DecisionStep {
  order: number;
  agent: string;
  action: string;
  summary: string;
  reasoning: string;
  confidence: number;
  params: Record<string, unknown>;
}

export interface HRReasoning {
  evaluation: string;
  score: number | null;
  verdict: "passed" | "failed" | "hard_pass" | "not_screened";
  details: string[];
  rejection_reasons: string[];
}

export interface CandidateActions {
  strategy: string;
  strategy_explanation: string;
  total_actions: number;
  actions: CandidateAction[];
}

export interface CandidateAction {
  action: string;
  confidence: number;
  reasoning: string;
  gap_skills: string[];
  match_score?: number;
}

export interface FailurePoint {
  stage: string;
  severity: "critical" | "high" | "medium";
  cause: string;
  detail: string;
  remediation: string;
}

export interface ConfidenceScore {
  overall: number;
  factors: {
    data_richness: number;
    gate_coverage: number;
    outcome_clarity: number;
  };
  interpretation: string;
}
