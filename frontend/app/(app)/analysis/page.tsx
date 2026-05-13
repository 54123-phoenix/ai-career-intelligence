"use client";

import { useState } from "react";
import type { CareerAnalysisResult } from "@/types/career";
import type { CareerPathData } from "@/types/simulation";
import { analyzeCareer, submitCareerFeedback, getCareerPath } from "@/lib/api/career";
import {
  StrategyComparison,
  CareerPathGraph,
  SimulationFeedback,
  CareerPlanTimeline,
} from "@/components/career";
import SkillRadar from "@/components/analysis/SkillRadar";

export default function AnalysisPage() {
  const [data, setData] = useState<CareerAnalysisResult | null>(null);
  const [pathData, setPathData] = useState<CareerPathData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const [userInput, setUserInput] = useState(
    "目标成为高级后端工程师，掌握 Python、FastAPI、PostgreSQL，有3年经验，本科，期望在北京工作"
  );

  async function handleRun() {
    setLoading(true);
    setError(null);
    setPathData(null);
    try {
      const [result, path] = await Promise.all([
        analyzeCareer({
          user_input: userInput,
          depth: "standard",
        }),
        getCareerPath(userInput).catch(() => null),
      ]);
      setData(result.data);
      setPathData(path);
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
      <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
        职业分析引擎
      </h1>
      <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
        解析职业画像、推荐匹配岗位、生成发展策略并模拟验证
      </p>

      {/* Input controls */}
      <div className="mb-6 rounded-xl border bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-slate-900">
        <div className="mb-4">
          <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
            职业目标、技能与经验
          </label>
          <textarea
            className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
            rows={2}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="描述您的职业目标、技能和经验..."
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400 dark:text-gray-500">
            输入越详细，分析结果越精准
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
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900/30 dark:bg-red-950/30 dark:text-red-300">
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
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                  : data.status === "partial"
                    ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
              }`}
            >
              {data.status === "success" ? "分析完成" : data.status === "partial" ? "部分完成" : "失败"}
            </span>
            <span className="text-gray-400 dark:text-gray-500">
              {data.recommendations.length} 个岗位推荐
            </span>
            <span className="text-gray-400 dark:text-gray-500">
              {data.strategies.length} 条候选策略
            </span>
            <span className="text-gray-400 dark:text-gray-500">
              {new Date(data.generatedAt).toLocaleString("zh-CN")}
            </span>
          </div>

          {/* Tabs */}
          <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-slate-800">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "bg-white text-gray-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
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
                {!!data.frontendData?.summary && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900 md:col-span-2">
                    <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                      {data.frontendData.summary.headline || "职业分析概览"}
                    </h3>
                    <div className="grid gap-4 md:grid-cols-3">
                      <StatCard
                        label="岗位匹配数"
                        value={data.recommendations.length}
                      />
                      <StatCard
                        label="最优策略得分"
                        value={`${((data.frontendData.summary.topStrategyScore || 0) * 100).toFixed(0)}%`}
                      />
                      <StatCard
                        label="模拟成功率"
                        value={`${((data.frontendData.summary.simulationSuccessRate || 0) * 100).toFixed(0)}%`}
                      />
                    </div>
                  </div>
                )}

                <div className="md:col-span-2">
                  <SkillRadar data={data} />
                </div>

                {data.userProfile && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
                    <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">用户画像</h3>
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-gray-500 dark:text-gray-400">工作经验</dt>
                        <dd className="text-gray-900 dark:text-gray-100">{data.userProfile.experienceYears} 年</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500 dark:text-gray-400">学历</dt>
                        <dd className="text-gray-900 dark:text-gray-100">{data.userProfile.educationLevel || "—"}</dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500 dark:text-gray-400">技能标签</dt>
                        <dd className="flex flex-wrap gap-1">
                          {data.userProfile.skills.map((s) => (
                            <span
                              key={s}
                              className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                            >
                              {s}
                            </span>
                          ))}
                        </dd>
                      </div>
                      <div>
                        <dt className="mb-1 text-gray-500 dark:text-gray-400">职业目标</dt>
                        <dd className="flex flex-wrap gap-1">
                          {data.userProfile.careerGoals.map((g, i) => (
                            <span
                              key={i}
                              className="rounded bg-green-50 px-1.5 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-300"
                            >
                              {g}
                            </span>
                          ))}
                        </dd>
                      </div>
                    </dl>
                  </div>
                )}

                {data.careerData && (
                  <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
                    <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">职业数据</h3>
                    <div className="mb-3 text-sm text-gray-500 dark:text-gray-400">
                      已解析 {data.careerData.totalEntries} 条数据
                    </div>
                    <div className="max-h-64 space-y-2 overflow-y-auto">
                      {data.careerData.entries.map((entry, i) => (
                        <div
                          key={i}
                          className="rounded border px-3 py-2 text-sm dark:border-gray-700"
                        >
                          <div className="font-medium text-gray-900 dark:text-white">{entry.jobTitle}</div>
                          <div className="text-xs text-gray-400 dark:text-gray-500">
                            {entry.requiredSkills.join(", ")}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "recommendations" && (
              <div className="space-y-4">
                {data.recommendations.map((job) => (
                  <div
                    key={job.id}
                    className="rounded-xl border bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-slate-900"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900 dark:text-white">{job.title}</h3>
                      <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                        匹配度 {job.matchScore}%
                      </span>
                    </div>
                    <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                      {job.company} · {job.location}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {job.requiredSkills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-slate-800 dark:text-gray-400"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                    {job.salaryRange && (
                      <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        薪资范围：¥{job.salaryRange[0]}K - ¥{job.salaryRange[1]}K
                      </div>
                    )}
                  </div>
                ))}
                {data.recommendations.length === 0 && (
                  <div className="rounded-xl border p-12 text-center text-gray-400 dark:border-gray-700">
                    暂无岗位推荐数据
                  </div>
                )}
              </div>
            )}

            {activeTab === "strategies" && !!data.frontendData?.strategyComparison && (
              <StrategyComparison
                data={data.frontendData.strategyComparison as any}
              />
            )}

            {activeTab === "plan" && (
              <CareerPlanTimeline
                plan={data.plan as any}
                timeline={data.frontendData?.actionTimeline as any}
              />
            )}

            {activeTab === "path" && (
              <CareerPathGraph data={pathData} />
            )}

            {activeTab === "simulation" && (
              <SimulationFeedback data={data.simulationResult as any} />
            )}

            {/* Feedback */}
            {data.status === "success" && (
              <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
                <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                  分析反馈
                </h3>
                {feedbackMessage && (
                  <div className="mb-3 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-900/30 dark:bg-green-950/30 dark:text-green-300">
                    {feedbackMessage}
                  </div>
                )}
                <div className="mb-3 flex items-center gap-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">评分：</span>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className={`text-xl transition-colors ${
                        star <= rating ? "text-yellow-400" : "text-gray-300 dark:text-gray-600"
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
                <textarea
                  className="mb-3 w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
                  rows={2}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="您的建议或意见..."
                />
                <button
                  onClick={async () => {
                    if (!rating) return;
                    setFeedbackLoading(true);
                    try {
                      await submitCareerFeedback({
                        analysis_id: data.id,
                        rating,
                        comments: comment,
                      });
                      setFeedbackMessage("感谢您的反馈！");
                      setRating(0);
                      setComment("");
                    } catch (e) {
                      setFeedbackMessage(e instanceof Error ? e.message : "提交失败");
                    } finally {
                      setFeedbackLoading(false);
                      setTimeout(() => setFeedbackMessage(null), 4000);
                    }
                  }}
                  disabled={feedbackLoading || !rating}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {feedbackLoading ? "提交中..." : "提交反馈"}
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {!data && !loading && !error && (
        <div className="rounded-xl border bg-white p-12 text-center text-gray-400 dark:border-gray-700 dark:bg-slate-900">
          输入您的职业目标与技能，点击“开始职业分析”获取岗位推荐与发展策略
        </div>
      )}
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-gray-50 p-4 text-center dark:bg-slate-800">
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}
