"use client";

interface Props {
  data: any;
}

export default function SimulationFeedbackPanel({ data }: Props) {
  if (!data) {
    return (
      <div className="rounded-lg border p-6 text-center text-gray-500 dark:border-gray-700">
        No simulation data available — run simulation first
      </div>
    );
  }

  // Legacy format (t008 SimulationFeedback)
  if (data.average_success_rate !== undefined) {
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
      <div className="rounded-lg border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Simulation Results</h3>

        <div className={`mb-6 rounded-lg ${bgColor} p-4`}>
          <div className="flex items-baseline gap-3">
            <span className={`text-3xl font-bold ${successColor}`}>
              {(data.average_success_rate * 100).toFixed(0)}%
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              average success rate across {data.total_rounds} simulation rounds
            </span>
          </div>
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            {data.successful_rounds} of {data.total_rounds} rounds succeeded
          </div>
          {data.recommendation && (
            <div className="mt-3 border-t pt-3 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300">
              {data.recommendation}
            </div>
          )}
        </div>

        {data.rounds && data.rounds.length > 0 && (
          <div className="mb-6 space-y-1.5">
            <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Per-Round Probabilities</div>
            {data.rounds.map((r: any) => (
              <div key={r.round_id} className="flex items-center gap-2 text-xs">
                <span className="w-8 text-right font-mono text-gray-400">
                  #{r.round_id}
                </span>
                <div className="h-5 flex-1 rounded bg-gray-100 dark:bg-slate-800">
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
        )}

        {data.aggregated_risks && Object.keys(data.aggregated_risks).length > 0 && (
          <div className="mb-4">
            <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Top Risks</div>
            <div className="space-y-1">
              {Object.entries(data.aggregated_risks)
                .sort((a: any, b: any) => b[1] - a[1])
                .slice(0, 5)
                .map(([risk, count]: any) => (
                  <div key={risk} className="flex items-center gap-2 text-sm">
                    <span className="text-red-500">⚠</span>
                    <span className="flex-1">{risk}</span>
                    <span className="font-mono text-gray-400">{count}×</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {data.aggregated_skill_gaps && Object.keys(data.aggregated_skill_gaps).length > 0 && (
          <div>
            <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">
              Recurring Skill Gaps
            </div>
            <div className="space-y-1">
              {Object.entries(data.aggregated_skill_gaps)
                .sort((a: any, b: any) => b[1] - a[1])
                .slice(0, 5)
                .map(([gap, count]: any) => (
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

  // New format (SimulationSummary)
  const successColor =
    (data.successProbability || 0) >= 0.7
      ? "text-green-600"
      : (data.successProbability || 0) >= 0.4
        ? "text-yellow-600"
        : "text-red-600";

  const bgColor =
    (data.successProbability || 0) >= 0.7
      ? "bg-green-50"
      : (data.successProbability || 0) >= 0.4
        ? "bg-yellow-50"
        : "bg-red-50";

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">模拟验证结果</h3>

      <div className={`mb-6 rounded-lg ${bgColor} p-4`}>
        <div className="flex items-baseline gap-3">
          <span className={`text-3xl font-bold ${successColor}`}>
            {((data.successProbability || 0) * 100).toFixed(0)}%
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            预估成功率
          </span>
        </div>
        {data.outcome && (
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            结果：{data.outcome}
          </div>
        )}
      </div>

      {data.recommendations && data.recommendations.length > 0 && (
        <div className="mb-4">
          <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">建议</div>
          <ul className="space-y-1">
            {data.recommendations.map((rec: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm">
                <span className="text-blue-500">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.confidenceScore && (
        <div>
          <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">置信度</div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-semibold">{((data.confidenceScore.overall || 0) * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
