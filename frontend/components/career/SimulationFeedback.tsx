"use client";

import type { SimulationFeedback } from "@/types/t008";

interface Props {
  data: SimulationFeedback | null;
}

export default function SimulationFeedbackPanel({ data }: Props) {
  if (!data) {
    return (
      <div className="rounded-lg border p-6 text-center text-gray-500">
        No simulation data available — run simulation first
      </div>
    );
  }

  const successColor =
    data.average_success_rate >= 0.7
      ? "text-green-600"
      : data.average_success_rate >= 0.4
        ? "text-yellow-600"
        : "text-red-600";

  const bgColor =
    data.average_success_rate >= 0.7
      ? "bg-green-50"
      : data.average_success_rate >= 0.4
        ? "bg-yellow-50"
        : "bg-red-50";

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold">Simulation Results</h3>

      {/* Summary card */}
      <div className={`mb-6 rounded-lg ${bgColor} p-4`}>
        <div className="flex items-baseline gap-3">
          <span className={`text-3xl font-bold ${successColor}`}>
            {(data.average_success_rate * 100).toFixed(0)}%
          </span>
          <span className="text-sm text-gray-500">
            average success rate across {data.total_rounds} simulation rounds
          </span>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          {data.successful_rounds} of {data.total_rounds} rounds succeeded
        </div>
        {data.recommendation && (
          <div className="mt-3 text-sm text-gray-700 border-t pt-3">
            {data.recommendation}
          </div>
        )}
      </div>

      {/* Rounds chart — horizontal bar per round */}
      <div className="mb-6 space-y-1.5">
        <div className="text-sm font-medium text-gray-500 mb-2">Per-Round Probabilities</div>
        {data.rounds.map((r) => (
          <div key={r.round_id} className="flex items-center gap-2 text-xs">
            <span className="w-8 text-right font-mono text-gray-400">
              #{r.round_id}
            </span>
            <div className="flex-1 h-5 rounded bg-gray-100">
              <div
                className={`h-5 rounded transition-all ${
                  r.success ? "bg-green-400" : "bg-red-300"
                }`}
                style={{ width: `${(r.success_probability * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="w-16 font-mono">
              {(r.success_probability * 100).toFixed(0)}%
            </span>
            <span className="w-8 text-center">
              {r.success ? "✓" : "✗"}
            </span>
          </div>
        ))}
      </div>

      {/* Aggregated risks */}
      {Object.keys(data.aggregated_risks).length > 0 && (
        <div className="mb-4">
          <div className="mb-2 text-sm font-medium text-gray-500">Top Risks</div>
          <div className="space-y-1">
            {Object.entries(data.aggregated_risks)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([risk, count]) => (
                <div key={risk} className="flex items-center gap-2 text-sm">
                  <span className="text-red-500">⚠</span>
                  <span className="flex-1">{risk}</span>
                  <span className="font-mono text-gray-400">{count}×</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Aggregated skill gaps */}
      {Object.keys(data.aggregated_skill_gaps).length > 0 && (
        <div>
          <div className="mb-2 text-sm font-medium text-gray-500">
            Recurring Skill Gaps
          </div>
          <div className="space-y-1">
            {Object.entries(data.aggregated_skill_gaps)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([gap, count]) => (
                <div key={gap} className="flex items-center gap-2 text-sm">
                  <span className="text-orange-500">●</span>
                  <span className="flex-1">{gap}</span>
                  <span className="font-mono text-gray-400">{count}×</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
