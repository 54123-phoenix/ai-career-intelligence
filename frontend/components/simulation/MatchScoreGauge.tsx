import type { MatchScoreSection } from "@/types/simulation";

const ringColors: Record<string, string> = {
  green: "stroke-green-500",
  yellow: "stroke-yellow-500",
  red: "stroke-red-500",
};

export function MatchScoreGauge({ data }: { data: MatchScoreSection }) {
  const pct = data.overall;
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">Match Score</h3>
      <div className="flex items-center gap-6">
        {/* Donut gauge */}
        <div className="relative h-24 w-24 flex-shrink-0">
          <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f3f4f6" strokeWidth="12" />
            <circle
              cx="50" cy="50" r="40" fill="none" strokeWidth="12"
              strokeLinecap="round"
              className={ringColors[data.gauge.color]}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold text-gray-900">{pct}%</span>
          </div>
        </div>
        {/* Breakdown bars */}
        <div className="flex-1 space-y-2">
          <Bar label="Skills" value={data.breakdown.skill_match} />
          <Bar label="Experience" value={data.breakdown.experience_fit} />
          <Bar label="Keywords" value={data.breakdown.keyword_overlap} />
        </div>
      </div>
      <p className="mt-3 text-center text-sm font-medium text-gray-600">{data.gauge.label} Match</p>
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 text-xs text-gray-600">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-gray-100">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all"
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-500 w-10 text-right">{value}%</span>
    </div>
  );
}
