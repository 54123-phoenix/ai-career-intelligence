"use client";

import { useEffect, useState } from "react";
import type { FinalT004Schema } from "@/types/simulation";
import { runSimulation, getSamples } from "@/lib/api";

import { SummaryCard } from "@/components/simulation/SummaryCard";
import { MatchScoreGauge } from "@/components/simulation/MatchScoreGauge";
import { SkillGapChart } from "@/components/simulation/SkillGapChart";
import { DecisionTimeline } from "@/components/simulation/DecisionTimeline";
import { HRExplanationPanel } from "@/components/simulation/HRExplanationPanel";

export default function SimulationReportPage() {
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
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Simulation Report</h1>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-end gap-4 rounded-xl border bg-white p-4 shadow-sm">
        <Select label="Resume" value={resumeId} onChange={setResumeId} options={samples?.resumes ?? {}} />
        <Select label="Job" value={jobId} onChange={setJobId} options={samples?.jobs ?? {}} />
        <div>
          <label className="block text-xs text-gray-500 mb-1">Strategy</label>
          <select
            className="rounded-lg border px-3 py-2 text-sm"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
          >
            <option value="aggressive">Aggressive</option>
            <option value="balanced">Balanced</option>
            <option value="conservative">Conservative</option>
          </select>
        </div>
        <button
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? "Running..." : "Run Simulation"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
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
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Recommendations</h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {data.recommendation_cards.map((card) => (
                  <div
                    key={`${card.priority}-${card.title}`}
                    className="rounded-lg border bg-gray-50 p-4"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                        card.type === "success" ? "bg-green-100 text-green-700" :
                        card.type === "warning" ? "bg-yellow-100 text-yellow-700" :
                        card.type === "action" ? "bg-blue-100 text-blue-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>
                        {card.type}
                      </span>
                      <span className="text-xs text-gray-400">P{card.priority}</span>
                    </div>
                    <h4 className="font-medium text-gray-900">{card.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{card.description}</p>
                    {card.action_label && (
                      <span className="inline-block mt-2 text-sm font-medium text-indigo-600">
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
  label, value, onChange, options,
}: {
  label: string; value: string; onChange: (v: string) => void;
  options: Record<string, string>;
}) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <select
        className="rounded-lg border px-3 py-2 text-sm min-w-[180px]"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {Object.entries(options).map(([id, name]) => (
          <option key={id} value={id}>{name}</option>
        ))}
      </select>
    </div>
  );
}
