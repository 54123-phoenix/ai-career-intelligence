"use client";

import { useState, useCallback } from "react";
import type { T009PipelineOutput } from "@/types/t009";
import { runT009Pipeline, submitT009Feedback, listT009Baselines } from "@/lib/t009-api";
import {
  StrategyComparison,
  CareerPathGraph,
  SimulationFeedback,
  CareerPlanTimeline,
} from "@/components/career";

const SAMPLE_DATASET: Record<string, unknown>[] = [
  {
    job_title: "Senior Backend Engineer",
    required_skills: ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
    optional_skills: ["AWS", "Terraform", "GraphQL"],
    growth_path: ["Junior Backend", "Backend Engineer", "Senior Backend", "Staff Engineer", "Principal"],
    level: "高级", salary_range: [400, 650], location: "北京",
    industry: "互联网", source: "sample",
  },
  {
    job_title: "Machine Learning Engineer",
    required_skills: ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning"],
    optional_skills: ["Kubernetes", "MLOps", "NLP"],
    growth_path: ["Data Analyst", "ML Engineer", "Senior MLE", "ML Architect"],
    level: "高级", salary_range: [500, 800], location: "上海",
    industry: "人工智能", source: "sample",
  },
  {
    job_title: "Frontend Tech Lead",
    required_skills: ["TypeScript", "React", "Next.js", "CSS", "System Design"],
    optional_skills: ["GraphQL", "Webpack", "React Native"],
    growth_path: ["Frontend Developer", "Senior Frontend", "Tech Lead", "Frontend Architect"],
    level: "高级", salary_range: [450, 700], location: "深圳",
    industry: "互联网", source: "sample",
  },
];

const SAMPLE_TRENDS: Record<string, unknown>[] = [
  {
    domain: "software_engineering",
    trend_name: "AI-assisted development",
    direction: "rising",
    confidence: 0.85,
    affected_skills: ["LLM Integration", "Prompt Engineering", "AI Code Review"],
    affected_roles: ["Backend Engineer", "Full Stack Developer"],
    growth_rate_pct: 35.0,
    source: "industry_report_2026",
    valid_until: "2027-01-01",
  },
  {
    domain: "software_engineering",
    trend_name: "Platform Engineering consolidation",
    direction: "rising",
    confidence: 0.75,
    affected_skills: ["Platform Engineering", "Internal Developer Platform", "DevEx"],
    affected_roles: ["DevOps Engineer", "Platform Engineer"],
    growth_rate_pct: 25.0,
    source: "industry_report_2026",
    valid_until: "2027-01-01",
  },
  {
    domain: "software_engineering",
    trend_name: "Remote-first tooling",
    direction: "rising",
    confidence: 0.70,
    affected_skills: ["Async Communication", "Remote Collaboration Tools"],
    affected_roles: ["Backend Engineer", "Engineering Manager"],
    growth_rate_pct: 15.0,
    source: "industry_report_2026",
    valid_until: "2027-01-01",
  },
];

interface ClickedNode {
  skill_name: string;
  description: string;
  strategy_note: string;
  risk_note: string;
}

export default function CareerGrowthV2Page() {
  const [data, setData] = useState<T009PipelineOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [clickedNode, setClickedNode] = useState<ClickedNode | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const [userInput, setUserInput] = useState(
    "目标成为高级后端工程师，掌握 Python、FastAPI、PostgreSQL，有3年经验，本科，期望在北京工作"
  );
  const [privacyLevel, setPrivacyLevel] = useState("basic");

  async function handleRun() {
    setLoading(true);
    setError(null);
    setFeedbackSubmitted(false);
    setClickedNode(null);
    try {
      const result = await runT009Pipeline({
        user_id: "demo-user-v2",
        user_input: userInput,
        career_dataset: SAMPLE_DATASET,
        industry_trends: SAMPLE_TRENDS,
        privacy_level: privacyLevel,
      });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const handleNodeClick = useCallback((nodeName: string) => {
    if (!data?.interactive_nodes) return;
    const nodeInfo = data.interactive_nodes[nodeName] as Record<string, string> | undefined;
    if (nodeInfo) {
      setClickedNode({
        skill_name: nodeName,
        description: nodeInfo.description || "",
        strategy_note: nodeInfo.strategy_note || "",
        risk_note: nodeInfo.risk_note || "",
      });
    }
  }, [data]);

  async function handleSubmitFeedback(rating: number, adopted: string) {
    try {
      await submitT009Feedback({
        user_id: "demo-user-v2",
        strategy_adopted: adopted,
        strategy_rating: rating,
        nodes_clicked: clickedNode ? [clickedNode.skill_name] : [],
        time_spent_sections: {},
        comments: "",
        preferences_updated: {},
        privacy_level: privacyLevel,
      });
      setFeedbackSubmitted(true);
    } catch (e) {
      console.error("Feedback submission failed:", e);
    }
  }

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "strategies", label: "Strategies" },
    { key: "plan", label: "Career Plan" },
    { key: "path", label: "Skill Path" },
    { key: "simulation", label: "Simulation" },
    { key: "trends", label: "Trends" },
    { key: "feedback", label: "Feedback" },
  ];

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            T009 Career Growth V2
          </h1>
          <p className="text-sm text-gray-500">
            RL optimization · diversity scoring · off-path detection · privacy-aware
          </p>
        </div>
        {data && (
          <span className="text-xs text-gray-400 font-mono">
            v{data.t009_version} · {data.elapsed_ms.toFixed(0)}ms
          </span>
        )}
      </div>

      {/* Input controls */}
      <div className="mb-6 rounded-xl border bg-white p-4 shadow-sm">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="md:col-span-2">
            <label className="mb-1 block text-xs text-gray-500">Career Goals, Skills, Experience</label>
            <textarea
              className="w-full rounded-lg border px-3 py-2 text-sm"
              rows={2}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500">Privacy Level</label>
            <select
              className="w-full rounded-lg border px-3 py-2 text-sm"
              value={privacyLevel}
              onChange={(e) => setPrivacyLevel(e.target.value)}
            >
              <option value="none">None — show all</option>
              <option value="basic">Basic — mask PII</option>
              <option value="full">Full — mask companies + salary</option>
            </select>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex gap-2 text-xs text-gray-400">
            <span>{SAMPLE_DATASET.length} dataset entries</span>
            <span>·</span>
            <span>{SAMPLE_TRENDS.length} industry trends</span>
            <span>·</span>
            <span>3 RL iterations</span>
            <span>·</span>
            <span>5-dim scoring</span>
          </div>
          <button
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            onClick={handleRun}
            disabled={loading}
          >
            {loading ? "Running T009 Pipeline..." : "Run T009 Pipeline V2"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
      )}

      {data && (
        <>
          {/* Status bar with T009-specific metrics */}
          <div className="mb-4 flex flex-wrap items-center gap-3 text-sm">
            <StatusBadge status={data.status} />
            <span className="text-gray-400">{data.job_recommendations.length} jobs</span>
            <span className="text-gray-400">{data.strategy_candidates.length} candidates</span>
            {data.diversity_metric && (
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                data.diversity_metric.overfitting_risk > 0.6
                  ? "bg-red-100 text-red-700"
                  : "bg-green-100 text-green-700"
              }`}>
                Diversity: {(data.diversity_metric.strategy_diversity * 100).toFixed(0)}%
              </span>
            )}
            {data.dynamic_weights && (
              <span className="text-xs text-gray-400">
                RL iter {data.dynamic_weights.iteration} · Δ={data.dynamic_weights.convergence_delta.toFixed(4)}
              </span>
            )}
            {data.off_path_flags.length > 0 && (
              <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                {data.off_path_flags.length} off-path warning(s)
              </span>
            )}
            {data.new_user_generated && (
              <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                Cold start profile
              </span>
            )}
            {data.privacy_mask && (
              <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                Privacy: {data.privacy_mask.anonymization_level}
              </span>
            )}
          </div>

          {/* Tabs */}
          <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="space-y-6">
            {activeTab === "overview" && (
              <div className="grid gap-6 md:grid-cols-2">
                {/* Summary */}
                {!!data.frontend_data?.summary && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm md:col-span-2">
                    <h3 className="mb-3 text-lg font-semibold">
                      {(data.frontend_data.summary as unknown as Record<string, unknown>).headline as string}
                    </h3>
                    <div className="grid gap-4 md:grid-cols-4">
                      <StatCard label="Job Matches" value={data.job_recommendations.length} />
                      <StatCard label="Top Strategy" value={`${(((data.frontend_data.summary as unknown as Record<string, unknown>).top_strategy_score as number) * 100).toFixed(0)}%`} />
                      <StatCard label="Sim Success" value={`${(((data.frontend_data.summary as unknown as Record<string, unknown>).simulation_success_rate as number) * 100).toFixed(0)}%`} />
                      <StatCard label="Diversity" value={`${((data.diversity_metric?.strategy_diversity ?? 0) * 100).toFixed(0)}%`} />
                    </div>
                  </div>
                )}

                {/* User Profile with baseline match */}
                {data.user_profile && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">User Profile</h3>
                    {data.baseline_strategy && (
                      <div className="mb-3 rounded bg-blue-50 px-3 py-2 text-xs text-blue-700">
                        Baseline match: {(data.baseline_strategy.match_confidence * 100).toFixed(0)}%
                        {data.new_user_generated && " (auto-generated)"}
                      </div>
                    )}
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Experience</dt>
                        <dd>{data.user_profile.experience_years} years</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Education</dt>
                        <dd>{data.user_profile.education_level || "—"}</dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500">Skills</dt>
                        <dd className="flex flex-wrap gap-1">
                          {data.user_profile.skills.map((s) => (
                            <span key={s} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">{s}</span>
                          ))}
                        </dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500">Goals</dt>
                        <dd className="flex flex-wrap gap-1">
                          {data.user_profile.career_goals.map((g, i) => (
                            <span key={i} className="rounded bg-green-50 px-1.5 py-0.5 text-xs text-green-700">{g}</span>
                          ))}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {/* Off-path warnings */}
                {data.off_path_flags.length > 0 && (
                  <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold text-yellow-800">
                      Off-Path Warnings
                    </h3>
                    <div className="space-y-2">
                      {data.off_path_flags.map((flag, i) => (
                        <div key={i} className="rounded border border-yellow-300 bg-white p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{flag.flag_type}</span>
                            <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                              flag.severity === "high"
                                ? "bg-red-100 text-red-700"
                                : flag.severity === "medium"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-blue-100 text-blue-700"
                            }`}>
                              {flag.severity}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-gray-600">{flag.description}</p>
                          {flag.recommendation && (
                            <p className="mt-1 text-xs text-blue-600">→ {flag.recommendation}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "strategies" && data.frontend_data && (
              <div className="space-y-6">
                <StrategyComparison data={data.frontend_data.strategy_comparison as import('@/types/t008').StrategyComparisonData} />
                {/* Diversity metric card */}
                {data.diversity_metric && (
                  <div className="rounded-lg border bg-white p-4 shadow-sm">
                    <h4 className="font-medium mb-2">Diversity Analysis</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Strategy Diversity</span>
                        <div className="text-xl font-bold">{(data.diversity_metric.strategy_diversity * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Overfitting Risk</span>
                        <div className={`text-xl font-bold ${data.diversity_metric.overfitting_risk > 0.6 ? "text-red-600" : "text-green-600"}`}>
                          {(data.diversity_metric.overfitting_risk * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Recommendation</span>
                        <div className="text-sm">{data.diversity_metric.recommendation}</div>
                      </div>
                    </div>
                  </div>
                )}
                {/* Dynamic weights display */}
                {data.dynamic_weights && (
                  <div className="rounded-lg border bg-white p-4 shadow-sm">
                    <h4 className="font-medium mb-2">
                      RL Weights (iter {data.dynamic_weights.iteration}, Δ={data.dynamic_weights.convergence_delta.toFixed(4)})
                    </h4>
                    <div className="flex gap-3">
                      {Object.entries(data.dynamic_weights.weights).map(([dim, w]) => (
                        <div key={dim} className="flex-1 rounded bg-gray-50 p-2 text-center">
                          <div className="text-xs text-gray-500">{dim}</div>
                          <div className="text-lg font-mono font-bold">{(w * 100).toFixed(0)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "plan" && (
              <CareerPlanTimeline
                plan={data.career_plan}
                timeline={data.frontend_data?.action_timeline as import('@/types/t008').ActionTimelineEntry[] ?? null}
              />
            )}

            {activeTab === "path" && (
              <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <CareerPathGraph data={data.visualization_data} />
                </div>
                {/* Interactive node details */}
                <div>
                  {clickedNode ? (
                    <div className="rounded-xl border bg-white p-6 shadow-sm sticky top-4">
                      <h3 className="mb-3 text-lg font-semibold">{clickedNode.skill_name}</h3>
                      <div className="space-y-3 text-sm">
                        <p>{clickedNode.description}</p>
                        <div className="rounded bg-blue-50 p-2 text-blue-700">
                          {clickedNode.strategy_note}
                        </div>
                        <div className="rounded bg-orange-50 p-2 text-orange-700">
                          {clickedNode.risk_note}
                        </div>
                      </div>
                      {!feedbackSubmitted && (
                        <div className="mt-4 space-y-2">
                          <button
                            className="w-full rounded bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700"
                            onClick={() => handleSubmitFeedback(1.0, data.strategy_list[0]?.strategy.strategy_name || "balanced")}
                          >
                            👍 This helps — adopt this strategy
                          </button>
                          <button
                            className="w-full rounded bg-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-300"
                            onClick={() => handleSubmitFeedback(0.3, data.strategy_list[0]?.strategy.strategy_name || "balanced")}
                          >
                            👎 Not relevant
                          </button>
                        </div>
                      )}
                      {feedbackSubmitted && (
                        <div className="mt-4 rounded bg-green-50 p-3 text-sm text-green-700">
                          Feedback sent — weights will update in next iteration
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rounded-xl border bg-white p-6 shadow-sm text-center text-gray-400 sticky top-4">
                      <div className="text-3xl mb-2">👆</div>
                      Click a skill node in the path graph to see strategy details and provide feedback
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === "simulation" && (
              <div className="space-y-6">
                <SimulationFeedback
                  data={data.simulation_feedback?.base_feedback ?? null}
                />
                {/* Off-path strategies detected */}
                {data.simulation_feedback?.off_path_strategies_detected &&
                  data.simulation_feedback.off_path_strategies_detected.length > 0 && (
                    <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
                      <h4 className="font-medium text-orange-800 mb-2">Off-Path Strategies Detected</h4>
                      <div className="text-sm text-orange-700">
                        The following strategies showed anomalous behavior in simulation:
                        {data.simulation_feedback.off_path_strategies_detected.map((id) => (
                          <span key={id} className="ml-2 rounded bg-orange-200 px-2 py-0.5 text-xs">{id}</span>
                        ))}
                      </div>
                    </div>
                  )}
                {/* RL convergence status */}
                {data.simulation_feedback && (
                  <div className="rounded-lg border bg-white p-4 shadow-sm">
                    <h4 className="font-medium mb-2">RL Optimization Status</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Iteration</span>
                        <div className="text-xl font-bold">{data.simulation_feedback.rl_iteration}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Weight Updates</span>
                        <div className="text-xl font-bold">{data.simulation_feedback.weight_updates_applied}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Converged</span>
                        <div className={`text-xl font-bold ${data.simulation_feedback.rl_converged ? "text-green-600" : "text-yellow-600"}`}>
                          {data.simulation_feedback.rl_converged ? "Yes" : "No"}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "trends" && (
              <div className="space-y-4">
                {/* Industry trends */}
                {data.trend_adjustments.length > 0 && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">Industry Trend Adjustments</h3>
                    <ul className="space-y-2">
                      {data.trend_adjustments.map((adj, i) => (
                        <li key={i} className="flex gap-2 text-sm">
                          <span className="text-blue-500">📈</span>
                          <span>{adj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Long-term outlook */}
                {data.long_term_outlook && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">12-24 Month Outlook</h3>
                    <p className="text-sm text-gray-700">{data.long_term_outlook}</p>
                  </div>
                )}

                {/* Baseline templates */}
                {data.baseline_strategy?.templates && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">Baseline Career Templates</h3>
                    <div className="grid gap-3 md:grid-cols-2">
                      {data.baseline_strategy.templates.map((t) => (
                        <div
                          key={t.template_id}
                          className={`rounded-lg border p-3 ${
                            t.template_id === data.baseline_strategy?.matched_template_id
                              ? "border-blue-300 bg-blue-50"
                              : ""
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">{t.target_role}</span>
                            <span className="text-xs text-gray-400">{t.domain}</span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {t.typical_skills.slice(0, 5).map((s) => (
                              <span key={s} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{s}</span>
                            ))}
                            {t.typical_skills.length > 5 && (
                              <span className="text-xs text-gray-400">+{t.typical_skills.length - 5} more</span>
                            )}
                          </div>
                          <div className="mt-1 text-xs text-gray-400">
                            {t.typical_timeline_months}mo · {t.recommended_strategies.join(", ")}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "feedback" && (
              <div className="space-y-6">
                {/* Feedback loop visualization */}
                {data.feedback_loop && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold">Feedback Loop State</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <FeedbackLoopItem
                        label="Retrieval ↔ Reviewer"
                        value={`${data.feedback_loop.retrieval_reviewer_iterations} iterations`}
                      />
                      <FeedbackLoopItem
                        label="Weight Updates"
                        value={`${data.feedback_loop.reviewer_weight_updates} updates`}
                      />
                      <FeedbackLoopItem
                        label="Simulation Feedback"
                        value={data.feedback_loop.simulation_feedback_applied ? "Applied" : "Pending"}
                        ok={data.feedback_loop.simulation_feedback_applied}
                      />
                      <FeedbackLoopItem
                        label="Rounds Run"
                        value={`${data.feedback_loop.simulation_rounds_run}`}
                      />
                      <FeedbackLoopItem
                        label="User Feedback"
                        value={data.feedback_loop.user_feedback_received ? "Received" : "Pending"}
                        ok={data.feedback_loop.user_feedback_received}
                      />
                      <FeedbackLoopItem
                        label="Pipeline Converged"
                        value={data.feedback_loop.pipeline_converged ? "Yes" : "No"}
                        ok={data.feedback_loop.pipeline_converged}
                      />
                    </div>
                    {data.feedback_loop.convergence_reason && (
                      <div className="mt-4 rounded bg-blue-50 p-3 text-sm text-blue-700">
                        {data.feedback_loop.convergence_reason}
                      </div>
                    )}
                  </div>
                )}

                {/* Strategy adoption feedback */}
                {data.strategy_list.length > 0 && !feedbackSubmitted && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold">Provide Feedback</h3>
                    <p className="mb-4 text-sm text-gray-500">
                      Your feedback flows back to the parser and reviewer agents, updating strategy weights.
                    </p>
                    <div className="space-y-3">
                      {data.strategy_list.slice(0, 3).map((s) => (
                        <div key={s.strategy.strategy_id} className="flex items-center justify-between rounded-lg border p-3">
                          <div>
                            <span className="font-medium capitalize">{s.strategy.strategy_name}</span>
                            <span className="ml-2 text-sm text-gray-500">
                              Score: {(s.overall_score * 100).toFixed(0)}%
                              {s.off_path && <span className="ml-1 text-orange-500">⚠ off-path</span>}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              className="rounded bg-green-100 px-3 py-1 text-sm text-green-700 hover:bg-green-200"
                              onClick={() => handleSubmitFeedback(0.9, s.strategy.strategy_name)}
                            >
                              Adopt
                            </button>
                            <button
                              className="rounded bg-gray-100 px-3 py-1 text-sm text-gray-600 hover:bg-gray-200"
                              onClick={() => handleSubmitFeedback(0.2, s.strategy.strategy_name)}
                            >
                              Skip
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {feedbackSubmitted && (
                  <div className="rounded-xl border border-green-200 bg-green-50 p-6 text-center shadow-sm">
                    <div className="text-2xl mb-2">👆</div>
                    <div className="font-medium text-green-800">Feedback Submitted</div>
                    <p className="text-sm text-green-600 mt-1">
                      Your preferences have been routed to the parser and reviewer agents.
                      Weights will reflect your input in the next pipeline run.
                    </p>
                  </div>
                )}
              </div>
            )}

            {data.errors.length > 0 && (
              <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
                <div className="font-medium mb-1">Warnings:</div>
                {data.errors.map((e, i) => (
                  <div key={i}>• {e}</div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {!data && !loading && !error && (
        <div className="rounded-xl border bg-white p-12 text-center text-gray-400">
          Enter your career goals and skills above, then click &quot;Run T009 Pipeline V2&quot;
          to see the full RL-optimized career growth analysis with diversity scoring
          and off-path detection.
        </div>
      )}
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: "bg-green-100 text-green-700",
    partial: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${colors[status] || colors.failed}`}>
      {status}
    </span>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-gray-50 p-4 text-center">
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

function FeedbackLoopItem({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
      <span className="text-gray-500">{label}</span>
      <span className={`font-medium ${ok === undefined ? "" : ok ? "text-green-600" : "text-yellow-600"}`}>
        {value}
      </span>
    </div>
  );
}
