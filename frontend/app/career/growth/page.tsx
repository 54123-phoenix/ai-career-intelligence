"use client";

import { useState } from "react";
import type { T008PipelineOutput } from "@/types/t008";
import { runT008Pipeline } from "@/lib/t008-api";
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
    level: "高级",
    salary_range: [400, 650],
    location: "北京",
    industry: "互联网",
    source: "sample",
  },
  {
    job_title: "Machine Learning Engineer",
    required_skills: ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning"],
    optional_skills: ["Kubernetes", "MLOps", "NLP"],
    growth_path: ["Data Analyst", "ML Engineer", "Senior MLE", "ML Architect"],
    level: "高级",
    salary_range: [500, 800],
    location: "上海",
    industry: "人工智能",
    source: "sample",
  },
  {
    job_title: "Frontend Tech Lead",
    required_skills: ["TypeScript", "React", "Next.js", "CSS", "System Design"],
    optional_skills: ["GraphQL", "Webpack", "React Native"],
    growth_path: ["Frontend Developer", "Senior Frontend", "Tech Lead", "Frontend Architect"],
    level: "高级",
    salary_range: [450, 700],
    location: "深圳",
    industry: "互联网",
    source: "sample",
  },
];

export default function CareerGrowthPage() {
  const [data, setData] = useState<T008PipelineOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("overview");

  const [userInput, setUserInput] = useState(
    "目标成为高级后端工程师，掌握 Python、FastAPI、PostgreSQL，有3年经验，本科，期望在北京工作"
  );

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const result = await runT008Pipeline({
        user_id: "demo-user",
        user_input: userInput,
        career_dataset: SAMPLE_DATASET,
      });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "strategies", label: "Strategies" },
    { key: "plan", label: "Career Plan" },
    { key: "path", label: "Skill Path" },
    { key: "simulation", label: "Simulation" },
    { key: "recommendations", label: "Recommendations" },
  ];

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">
        T008 Career Growth System
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        6-agent pipeline: parse → retrieve → review → architect → simulate → frontend
      </p>

      {/* Input controls */}
      <div className="mb-6 rounded-xl border bg-white p-4 shadow-sm">
        <div className="mb-4">
          <label className="mb-1 block text-xs text-gray-500">
            Career Goals, Skills, Experience
          </label>
          <textarea
            className="w-full rounded-lg border px-3 py-2 text-sm"
            rows={2}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Describe your career goals, skills, and experience..."
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Dataset: {SAMPLE_DATASET.length} sample career entries loaded
          </span>
          <button
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            onClick={handleRun}
            disabled={loading}
          >
            {loading ? "Running Pipeline..." : "Run T008 Pipeline"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Status bar */}
          <div className="mb-4 flex items-center gap-4 text-sm">
            <span
              className={`rounded px-2 py-0.5 text-xs font-medium ${
                data.status === "success"
                  ? "bg-green-100 text-green-700"
                  : data.status === "partial"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-red-100 text-red-700"
              }`}
            >
              {data.status}
            </span>
            <span className="text-gray-400">
              {data.job_recommendations.length} job matches
            </span>
            <span className="text-gray-400">
              {data.strategy_list.length} strategies scored
            </span>
            <span className="text-gray-400">
              {data.simulation_feedback?.total_rounds ?? 0} simulation rounds
            </span>
            <span className="text-gray-400">
              {data.elapsed_ms.toFixed(0)}ms
            </span>
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
                {!!data.frontend_data?.summary && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm md:col-span-2">
                    <h3 className="mb-3 text-lg font-semibold">
                      {(data.frontend_data.summary as unknown as Record<string, unknown>).headline as string}
                    </h3>
                    <div className="grid gap-4 md:grid-cols-3">
                      <StatCard
                        label="Skill Matches"
                        value={data.job_recommendations.length}
                      />
                      <StatCard
                        label="Top Strategy"
                        value={`${((data.frontend_data.summary as unknown as Record<string, unknown>).top_strategy_score as number * 100).toFixed(0)}%`}
                      />
                      <StatCard
                        label="Simulation Success"
                        value={`${((data.frontend_data.summary as unknown as Record<string, unknown>).simulation_success_rate as number * 100).toFixed(0)}%`}
                      />
                    </div>
                  </div>
                )}

                {data.user_profile && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">User Profile</h3>
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
                            <span
                              key={s}
                              className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700"
                            >
                              {s}
                            </span>
                          ))}
                        </dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500">Goals</dt>
                        <dd className="flex flex-wrap gap-1">
                          {data.user_profile.career_goals.map((g, i) => (
                            <span
                              key={i}
                              className="rounded bg-green-50 px-1.5 py-0.5 text-xs text-green-700"
                            >
                              {g}
                            </span>
                          ))}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {data.career_data && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">Career Dataset</h3>
                    <div className="text-sm text-gray-500 mb-3">
                      {data.career_data.total_entries} entries parsed
                    </div>
                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {data.career_data.entries.map((entry, i) => (
                        <div
                          key={i}
                          className="rounded border px-3 py-2 text-sm"
                        >
                          <div className="font-medium">{entry.job_title}</div>
                          <div className="text-xs text-gray-400">
                            {entry.required_skills.join(", ")}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "strategies" && data.frontend_data && (
              <StrategyComparison
                data={data.frontend_data.strategy_comparison as import('@/types/t008').StrategyComparisonData}
              />
            )}

            {activeTab === "plan" && (
              <CareerPlanTimeline
                plan={data.career_plan}
                timeline={data.frontend_data?.action_timeline as import('@/types/t008').ActionTimelineEntry[] ?? null}
              />
            )}

            {activeTab === "path" && (
              <CareerPathGraph data={data.visualization_data} />
            )}

            {activeTab === "simulation" && (
              <SimulationFeedback data={data.simulation_feedback} />
            )}

            {activeTab === "recommendations" &&
              !!data.frontend_data?.recommendations && (
                <div className="rounded-xl border bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-lg font-semibold">
                    Recommendations
                  </h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {(data.frontend_data.recommendations as unknown[]).map((rec: any) => (
                      <div
                        key={`${rec.priority}-${rec.title}`}
                        className="rounded-lg border bg-gray-50 p-4"
                      >
                        <div className="mb-1 flex items-center gap-2">
                          <span
                            className={`rounded px-2 py-0.5 text-xs font-medium ${
                              rec.type === "strategy"
                                ? "bg-blue-100 text-blue-700"
                                : rec.type === "simulation"
                                  ? "bg-green-100 text-green-700"
                                  : "bg-orange-100 text-orange-700"
                            }`}
                          >
                            {rec.type}
                          </span>
                          <span className="text-xs text-gray-400">
                            P{rec.priority}
                          </span>
                        </div>
                        <h4 className="font-medium text-gray-900">
                          {rec.title}
                        </h4>
                        <p className="mt-1 text-sm text-gray-600">
                          {rec.description}
                        </p>
                      </div>
                    ))}
                  </div>
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
          Enter your career goals and skills above, then click &quot;Run T008 Pipeline&quot;
          to see the full 6-agent career growth analysis.
        </div>
      )}
    </main>
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
