"use client";

import type { CareerPlan, ActionTimelineEntry } from "@/types/t008";

interface Props {
  plan: CareerPlan | null;
  timeline: ActionTimelineEntry[] | null;
}

const PHASE_COLORS: Record<string, string> = {
  preparation: "#3498db",
  application: "#2ecc71",
  interview: "#f39c12",
  negotiation: "#e74c3c",
  onboarding: "#9b59b6",
};

export default function CareerPlanTimeline({ plan, timeline }: Props) {
  if (!plan || !timeline || !timeline.length) {
    return (
      <div className="rounded-lg border p-6 text-center text-gray-500">
        No career plan data available
      </div>
    );
  }

  const maxDay = Math.max(...timeline.map((t) => t.end_day), 1);

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="text-lg font-semibold">
          {plan.selected_strategy ? (
            <>
              Career Plan —{" "}
              <span className="capitalize">
                {plan.selected_strategy.strategy.strategy_name}
              </span>
            </>
          ) : (
            "Career Plan"
          )}
        </h3>
        <span className="text-sm text-gray-500">
          {plan.total_duration_days} days total
        </span>
      </div>

      {/* Gantt-like timeline */}
      <div className="space-y-3">
        {timeline.map((step) => {
          const leftPct = (step.start_day / maxDay) * 100;
          const widthPct = (step.duration_days / maxDay) * 100;
          const color = PHASE_COLORS[step.phase] || "#95a5a6";

          return (
            <div key={step.step_number}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium">
                  {step.step_number}. {step.title}
                </span>
                <span className="text-xs text-gray-400">
                  Days {step.start_day}–{step.end_day} ({step.duration_days}d)
                </span>
              </div>
              <div className="relative h-7 rounded bg-gray-100">
                <div
                  className="absolute h-7 rounded"
                  style={{
                    left: `${leftPct}%`,
                    width: `${Math.max(widthPct, 3)}%`,
                    backgroundColor: color,
                    opacity: 0.85,
                  }}
                />
              </div>
              <div className="mt-1 flex flex-wrap gap-1">
                <span
                  className="rounded px-1.5 py-0.5 text-xs text-white"
                  style={{ backgroundColor: color }}
                >
                  {step.phase}
                </span>
                {step.milestones.map((m, i) => (
                  <span
                    key={i}
                    className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                  >
                    🏁 {m}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Risk & Skill Gaps */}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {plan.risk_points.length > 0 && (
          <div>
            <div className="mb-2 text-sm font-medium text-red-600">Risks</div>
            <ul className="space-y-1">
              {plan.risk_points.map((risk, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-red-400">•</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {plan.skill_gaps.length > 0 && (
          <div>
            <div className="mb-2 text-sm font-medium text-orange-600">
              Skill Gaps
            </div>
            <div className="flex flex-wrap gap-1.5">
              {plan.skill_gaps.map((gap) => (
                <span
                  key={gap}
                  className="rounded bg-orange-50 px-2 py-0.5 text-xs text-orange-700"
                >
                  {gap}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recommendation */}
      {plan.recommendation && (
        <div className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
          {plan.recommendation}
        </div>
      )}

      {/* Success rate */}
      <div className="mt-4 flex items-center gap-2">
        <span className="text-sm text-gray-500">Estimated success rate:</span>
        <span className="text-sm font-semibold">
          {(plan.estimated_success_rate * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
