import type { SummarySection } from "@/types/simulation";

const badgeStyles: Record<string, string> = {
  success: "bg-green-100 text-green-800 border-green-300",
  failure: "bg-red-100 text-red-800 border-red-300",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-300",
};

export function SummaryCard({ data }: { data: SummarySection }) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <span className={`inline-block rounded-full border px-3 py-1 text-sm font-medium ${badgeStyles[data.badge]}`}>
            {data.badge.toUpperCase()}
          </span>
          <h2 className="mt-3 text-xl font-semibold text-gray-900">{data.headline}</h2>
          <p className="mt-1 text-gray-600">
            {data.candidate_name} → {data.job_title} @ {data.company}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-4 border-t pt-4">
        <Stat label="Success P" value={`${(data.stats.success_probability * 100).toFixed(0)}%`} />
        <Stat label="Steps to Offer" value={data.stats.time_to_offer_steps > 0 ? String(data.stats.time_to_offer_steps) : "—"} />
        <Stat label="Reward" value={data.stats.total_reward.toFixed(2)} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
