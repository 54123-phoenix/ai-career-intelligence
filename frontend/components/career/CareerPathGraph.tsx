"use client";

interface Props {
  data: any;
}

const LEVEL_COLORS: Record<string, string> = {
  beginner: "#3498db",
  intermediate: "#2ecc71",
  advanced: "#f39c12",
  expert: "#e74c3c",
};

const EVENT_ICONS: Record<string, string> = {
  skill_acquisition: "📚",
  application: "📤",
  interview: "🎯",
  offer: "🎉",
  milestone: "🏁",
};

function SkillNodeCard({ node }: { node: any }) {
  const color = LEVEL_COLORS[node.level] || "#95a5a6";
  return (
    <div
      className="rounded-lg border px-4 py-3"
      style={{ borderLeftColor: color, borderLeftWidth: 4 }}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{node.skill_name}</span>
        <span
          className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: color }}
        >
          {node.level}
        </span>
      </div>
      {node.dependencies.length > 0 && (
        <div className="mt-1 text-xs text-gray-500">
          Requires: {node.dependencies.join(", ")}
        </div>
      )}
      {node.estimated_hours > 0 && (
        <div className="mt-1 text-xs text-gray-400">
          ~{node.estimated_hours}h to acquire
        </div>
      )}
    </div>
  );
}

function TimelineNodeRow({ node }: { node: any }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <div className="mt-0.5 text-lg">{EVENT_ICONS[node.event_type] || "●"}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400">Week {node.week}</span>
          <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
            {node.event_type.replace("_", " ")}
          </span>
        </div>
        <div className="font-medium">{node.label}</div>
        {node.details && (
          <div className="text-sm text-gray-500">{node.details}</div>
        )}
      </div>
    </div>
  );
}

export default function CareerPathGraph({ data }: Props) {
  if (!data || (!data.skill_nodes.length && !data.timeline_nodes.length)) {
    return (
      <div className="rounded-lg border p-6 text-center text-gray-500">
        No career path data available
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Skill Tree */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold">Skill Tree</h3>
        {data.primary_path.length > 0 && (
          <div className="mb-4">
            <div className="mb-2 text-sm text-gray-500">Primary Path</div>
            <div className="flex flex-wrap items-center gap-2">
              {data.primary_path.map((skill: any, i: number) => (
                <span key={skill}>
                  <span className="rounded bg-blue-50 px-2 py-1 text-sm font-medium text-blue-700">
                    {skill}
                  </span>
                  {i < data.primary_path.length - 1 && (
                    <span className="mx-1 text-gray-400">→</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {data.skill_nodes.map((node: any) => (
            <SkillNodeCard key={node.skill_name} node={node} />
          ))}
        </div>

        {data.skill_edges.length > 0 && (
          <div className="mt-4 text-xs text-gray-400">
            Dependencies:{" "}
            {data.skill_edges
              .map((edge: any[]) => `${edge[0]} → ${edge[1]}`)
              .join(", ")}
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold">Career Timeline</h3>
        <div className="divide-y">
          {data.timeline_nodes.map((node: any, i: number) => (
            <TimelineNodeRow key={i} node={node} />
          ))}
        </div>
      </div>
    </div>
  );
}
