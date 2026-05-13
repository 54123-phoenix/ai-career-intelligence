"use client";

import { useEffect, useState } from "react";
import type { FinalT004Schema } from "@/types/simulation";
import { runSimulation, getSamples } from "@/lib/api";

import { SummaryCard } from "@/components/simulation/SummaryCard";
import { MatchScoreGauge } from "@/components/simulation/MatchScoreGauge";
import { SkillGapChart } from "@/components/simulation/SkillGapChart";
import { DecisionTimeline } from "@/components/simulation/DecisionTimeline";
import { HRExplanationPanel } from "@/components/simulation/HRExplanationPanel";

export default function SimulationPage() {
  const [data, setData] = useState<FinalT004Schema | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [resumeId, setResumeId] = useState("res-001");
  const [jobId, setJobId] = useState("job-001");
  const [strategy, setStrategy] = useState("balanced");

  const [samples, setSamples] = useState<{ resumes: Record<string, string>; jobs: Record<string, string> } | null>(null);

  useEffect(() => {
    getSamples().then(setSamples).catch(() => {});
  }, []);

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const result = await runSimulation({ resume_id: resumeId, job_id: jobId, strategy });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
        职业模拟与演化
      </h1>
      <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
        模拟不同职业路径上的成长、晋升与技能变化，对比策略优劣
      </p>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-end gap-4 rounded-xl border bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-slate-900">
        <Select label="简历" value={resumeId} onChange={setResumeId} options={samples?.resumes ?? {}} />
        <Select label="目标岗位" value={jobId} onChange={setJobId} options={samples?.jobs ?? {}} />
        <div>
          <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">策略风格</label>
          <select
            className="rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
          >
            <option value="aggressive">激进</option>
            <option value="balanced">均衡</option>
            <option value="conservative">保守</option>
          </select>
        </div>
        <button
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? "模拟运行中..." : "运行职业模拟"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900/30 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-6">
          <SummaryCard data={data.summary} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <MatchScoreGauge data={data.match_score} />
            <SkillGapChart data={data.skill_gap_chart} />
          </div>
          <DecisionTimeline data={data.timeline} />
          <HRExplanationPanel
            hr={data.hr_reasoning}
            candidate={data.candidate_actions}
            failures={data.failure_points}
            confidence={data.confidence_score}
          />

          {/* Recommendation Cards */}
          {data.recommendation_cards.length > 0 && (
            <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">策略建议</h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {data.recommendation_cards.map((card) => (
                  <div
                    key={`${card.priority}-${card.title}`}
                    className="rounded-lg border bg-gray-50 p-4 dark:border-gray-700 dark:bg-slate-800"
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-medium ${
                          card.type === "success"
                            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                            : card.type === "warning"
                              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                              : card.type === "action"
                                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                                : "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-gray-300"
                        }`}
                      >
                        {card.type}
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500">P{card.priority}</span>
                    </div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{card.title}</h4>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{card.description}</p>
                    {card.action_label && (
                      <span className="mt-2 inline-block text-sm font-medium text-indigo-600 dark:text-indigo-400">
                        → {card.action_label}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Record<string, string>;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">{label}</label>
      <select
        className="min-w-[180px] rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {Object.entries(options).map(([id, name]) => (
          <option key={id} value={id}>
            {name}
          </option>
        ))}
      </select>
    </div>
  );
}
