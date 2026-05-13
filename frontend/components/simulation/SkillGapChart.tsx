import type { SkillGapChartSection } from "@/types/simulation";

const categoryColors: Record<string, string> = {
  required: "bg-blue-500",
  optional: "bg-purple-400",
  bonus: "bg-emerald-400",
};

export function SkillGapChart({ data }: { data: SkillGapChartSection }) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{data.title}</h3>
      <div className="grid grid-cols-2 gap-6">
        <SkillColumn title="Matched" skills={data.matched} />
        <SkillColumn title="Missing" skills={data.missing} />
      </div>
    </div>
  );
}

function SkillColumn({ title, skills }: { title: string; skills: { name: string; value: number; category: string }[] }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-gray-500">{title} ({skills.length})</h4>
      <div className="space-y-1.5">
        {skills.map((s) => (
          <div key={s.name} className="flex items-center gap-2">
            <span className="w-24 truncate text-sm text-gray-700" title={s.name}>{s.name}</span>
            <div className="flex-1 h-1.5 rounded-full bg-gray-100">
              <div
                className={`h-1.5 rounded-full ${categoryColors[s.category] || "bg-gray-400"}`}
                style={{ width: `${s.value}%` }}
              />
            </div>
            <span className="text-xs text-gray-400 w-6 text-right">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
