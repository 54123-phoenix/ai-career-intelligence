"use client";

import { useState } from "react";
import type { CareerAnalysisOutput } from "@/types/career";
import { analyzeCareer } from "@/lib/career-api";
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

export default function AnalysisPage() {
  const [data, setData] = useState<CareerAnalysisOutput | null>(null);
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
      const result = await analyzeCareer({
        user_id: "demo-user",
        user_input: userInput,
        career_dataset: SAMPLE_DATASET,
        privacy_level: "basic",
      });
      setData(result.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const tabs = [
    { key: "overview", label: "概览" },
    { key: "recommendations", label: "职业推荐" },
    { key: "strategies", label: "策略对比" },
    { key: "plan", label: "职业规划" },
    { key: "path", label: "技能路径" },
    { key: "simulation", label: "模拟验证" },
  ];

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">
        职业分析引擎
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        解析职业画像、推荐匹配岗位、生成发展策略并模拟验证
      </p>

      {/* Input controls */}
      <div className="mb-6 rounded-xl border bg-white p-4 shadow-sm">
        <div className="mb-4">
          <label className="mb-1 block text-xs text-gray-500">
            职业目标、技能与经验
          </label>
          <textarea
            className="w-full rounded-lg border px-3 py-2 text-sm"
            rows={2}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="描述您的职业目标、技能和经验..."
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            已加载 {SAMPLE_DATASET.length} 条示例职业数据
          </span>
          <button
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            onClick={handleRun}
            disabled={loading}
          >
            {loading ? "分析中..." : "开始职业分析"}
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
              {data.status === "success" ? "分析完成" : data.status === "partial" ? "部分完成" : "失败"}
            </span>
            <span className="text-gray-400">
              {data.job_recommendations.length} 个岗位推荐
            </span>
            <span className="text-gray-400">
              {data.strategy_candidates.length} 条候选策略
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
                        label="岗位匹配数"
                        value={data.job_recommendations.length}
                      />
                      <StatCard
                        label="最优策略得分"
                        value={`${((data.frontend_data.summary as unknown as Record<string, unknown>).top_strategy_score as number * 100).toFixed(0)}%`}
                      />
                      <StatCard
                        label="模拟成功率"
                        value={`${((data.frontend_data.summary as unknown as Record<string, unknown>).simulation_success_rate as number * 100).toFixed(0)}%`}
                      />
                    </div>
                  </div>
                )}

                {data.user_profile && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="mb-3 text-lg font-semibold">用户画像</h3>
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">工作经验</dt>
                        <dd>{data.user_profile.experience_years} 年</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">学历</dt>
                        <dd>{data.user_profile.education_level || "—"}</dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500">技能标签</dt>
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
                        <dt className="mb-1 text-gray-500">职业目标</dt>
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
                    <h3 className="mb-3 text-lg font-semibold">职业数据</h3>
                    <div className="text-sm text-gray-500 mb-3">
                      已解析 {data.career_data.total_entries} 条数据
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
              <SimulationFeedback data={data.simulation_feedback?.base_feedback ?? null} />
            )}

            {activeTab === "recommendations" &&
              !!data.frontend_data?.recommendations && (
                <div className="rounded-xl border bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-lg font-semibold">
                    分析与建议
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
                <div className="font-medium mb-1">提示：</div>
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
          输入您的职业目标与技能，点击“开始职业分析”获取岗位推荐与发展策略
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
