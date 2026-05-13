/** Career Domain Types — 职业分析与模拟的业务类型定义
 *
 * 本文件从底层任务编号类型（t008/t010）重新导出业务语义类型，
 * 前端组件与页面应优先 import 此处，避免直接依赖构建产物类型。
 */

export type {
  UserProfile,
  CareerData,
  CareerDataEntry,
  JobRecommendation,
  StrategyCandidate,
  ScoredStrategy as ScoredCareerStrategy,
  CareerPlan,
  PlanStep,
  VisualizationGraph,
  SimulationFeedback,
  FrontendData,
  FrontendSummary,
  StrategyComparisonData,
  StrategyComparisonEntry,
  ActionTimelineEntry,
  RecommendationItem,
  SimulationChartData,
  SimulationChartRound,
} from "./t008";

export type {
  T010PipelineOutput as CareerAnalysisOutput,
} from "./t010";
