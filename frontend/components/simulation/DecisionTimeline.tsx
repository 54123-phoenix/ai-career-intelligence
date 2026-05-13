import type { TimelineSection } from '@/types/simulation';

const phaseIcons: Record<string, string> = {
  applied: '📄',
  screened: '🔍',
  interview: '💬',
  offer: '📨',
  accepted: '✅',
  rejected: '❌',
};

const actorBadges: Record<string, string> = {
  candidate: 'bg-blue-50 text-blue-700',
  hr: 'bg-purple-50 text-purple-700',
  interview: 'bg-orange-50 text-orange-700',
  system: 'bg-gray-50 text-gray-600',
};

export function DecisionTimeline({ data }: { data: TimelineSection }) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">
        Decision Timeline ({data.total_steps} steps)
      </h3>
      <div className="relative">
        {data.events.map((ev, i) => (
          <div key={i} className="flex gap-4 pb-4">
            {/* Vertical line + dot */}
            <div className="flex flex-col items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-200 bg-white text-sm">
                {phaseIcons[ev.phase] || '●'}
              </div>
              {i < data.events.length - 1 && <div className="w-0.5 flex-1 bg-gray-200" />}
            </div>
            {/* Content */}
            <div className="flex-1 pb-2">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`rounded px-2 py-0.5 text-xs font-medium ${actorBadges[ev.actor] || ''}`}
                >
                  {ev.actor}
                </span>
                <span className="text-sm font-medium text-gray-900">{ev.action_label}</span>
                {ev.score != null && (
                  <span className="text-xs font-mono text-gray-500">
                    score: {ev.score.toFixed(2)}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600">{ev.reasoning}</p>
              <p className="mt-1 text-xs text-gray-400">
                confidence: {(ev.confidence ?? 0).toFixed(2)} · {ev.timestamp?.slice(0, 19) || ''}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
