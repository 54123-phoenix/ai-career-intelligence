/** T010 TypeScript types — Lightweight core layer, upgrade-ready. */

import type {
  UserProfile,
  CareerData,
  JobRecommendation,
  StrategyCandidate,
  CareerPlan,
  VisualizationGraph,
} from './t008';
import type {
  BaselineStrategy,
  OffPathFlag,
  DiversityMetric,
  DynamicWeights,
  ScoredStrategyV2,
  PrivacyMask,
  FeedbackLoopState,
  T009SimulationFeedback,
} from './t009';

export interface UpgradeInterface {
  agent: string;
  core_capability: string;
  upgrade_hooks: string[];
  upgrade_notes: string;
  version: string;
}

export interface T010PipelineOutput {
  execution_id: string;
  status: 'success' | 'partial' | 'failed';
  errors: string[];

  // Stage 1
  user_profile: UserProfile | null;
  career_data: CareerData | null;
  baseline_strategy: BaselineStrategy | null;
  off_path_flags: OffPathFlag[];

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
  interactive_nodes: Record<string, Record<string, unknown>>;

  // Stage 5
  simulation_feedback: T009SimulationFeedback | null;
  refined_strategy_list: ScoredStrategyV2[] | null;

  // Stage 6
  frontend_data: Record<string, unknown>;
  privacy_mask: PrivacyMask | null;

  // Feedback
  feedback_loop: FeedbackLoopState | null;

  // Upgrade interfaces
  upgrade_interfaces: Record<string, UpgradeInterface>;

  // Meta
  elapsed_ms: number;
  generated_at: string;
  version: string;
}
