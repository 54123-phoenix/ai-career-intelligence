'use client';

import type { StrategyComparisonData } from '@/types/career';

interface Props {
  data: StrategyComparisonData | null;
}

const DIMENSION_LABELS: Record<string, string> = {
  success_rate: 'Success Rate',
  match_degree: 'Profile Match',
  growth_cycle: 'Growth Speed',
  skill_adaptability: 'Skill Adaptability',
};

const STRATEGY_COLORS = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'];

export default function StrategyComparison({ data }: Props) {
  if (!data || !data.strategies.length) {
    return (
      <div className="rounded-lg border p-6 text-center text-gray-500">
        No strategy data available
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold">Strategy Comparison</h3>

      {/* Bar chart */}
      <div className="mb-6 space-y-4">
        {data.strategies.map((s, i) => (
          <div key={s.name} className="flex items-center gap-3">
            <span
              className="w-24 text-sm font-medium"
              style={{ color: STRATEGY_COLORS[i % STRATEGY_COLORS.length] }}
            >
              {s.name}
            </span>
            <div className="flex-1">
              <div className="h-6 w-full rounded bg-gray-100">
                <div
                  className="h-6 rounded transition-all"
                  style={{
                    width: `${(s.overall * 100).toFixed(0)}%`,
                    backgroundColor: STRATEGY_COLORS[i % STRATEGY_COLORS.length],
                  }}
                />
              </div>
            </div>
            <span className="w-12 text-right text-sm font-mono">
              {(s.overall * 100).toFixed(0)}%
            </span>
            <span className="w-6 text-center text-xs text-gray-400">#{s.rank}</span>
          </div>
        ))}
      </div>

      {/* Dimension breakdown table */}
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="pb-2 font-medium">Strategy</th>
            {data.dimensions.map((dim) => (
              <th key={dim} className="pb-2 font-medium">
                {DIMENSION_LABELS[dim] || dim}
              </th>
            ))}
            <th className="pb-2 text-right font-medium">Overall</th>
          </tr>
        </thead>
        <tbody>
          {data.strategies.map((s, i) => (
            <tr key={s.name} className="border-b last:border-0">
              <td
                className="py-2 font-medium"
                style={{ color: STRATEGY_COLORS[i % STRATEGY_COLORS.length] }}
              >
                {s.name}
              </td>
              <td className="py-2 font-mono">{(s.success_rate * 100).toFixed(0)}%</td>
              <td className="py-2 font-mono">{(s.match_degree * 100).toFixed(0)}%</td>
              <td className="py-2 font-mono">{(s.growth_cycle * 100).toFixed(0)}%</td>
              <td className="py-2 font-mono">{(s.skill_adaptability * 100).toFixed(0)}%</td>
              <td className="py-2 text-right font-mono font-semibold">
                {(s.overall * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
