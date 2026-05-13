import type {
  HRReasoning,
  CandidateActions,
  FailurePoint,
  ConfidenceScore,
} from '@/types/simulation';

const verdictStyles: Record<string, string> = {
  passed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  hard_pass: 'bg-red-200 text-red-900',
  not_screened: 'bg-gray-100 text-gray-600',
};

const severityIcons: Record<string, string> = {
  critical: '🔴',
  high: '🟠',
  medium: '🟡',
};

export function HRExplanationPanel({
  hr,
  candidate,
  failures,
  confidence,
}: {
  hr: HRReasoning;
  candidate: CandidateActions;
  failures: FailurePoint[];
  confidence: ConfidenceScore;
}) {
  return (
    <div className="space-y-4">
      {/* HR Verdict */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-gray-900">HR Verdict</h3>
        <div className="flex items-center gap-3 mb-3">
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${verdictStyles[hr.verdict]}`}
          >
            {hr.verdict.replace('_', ' ').toUpperCase()}
          </span>
          {hr.score != null && (
            <span className="text-xl font-bold text-gray-900">{hr.score.toFixed(3)}</span>
          )}
        </div>
        <p className="mb-2 text-sm text-gray-700">{hr.evaluation}</p>
        {hr.details.length > 0 && (
          <ul className="list-disc pl-5 text-sm text-gray-600 space-y-0.5">
            {hr.details.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Candidate Strategy */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-gray-900">Candidate Strategy</h3>
        <p className="mb-3 text-sm text-gray-700">{candidate.strategy_explanation}</p>
        <div className="space-y-2">
          {candidate.actions.map((a, i) => (
            <div key={i} className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
              <span className="mt-0.5 rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                {a.action}
              </span>
              <div>
                <p className="text-sm text-gray-700">{a.reasoning}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  confidence: {a.confidence.toFixed(2)}
                  {a.match_score != null && ` · match: ${(a.match_score * 100).toFixed(0)}%`}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Failure Points */}
      {failures.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold text-red-900">Failure Points</h3>
          {failures.map((fp, i) => (
            <div key={i} className="mb-3 last:mb-0 rounded-lg bg-white p-4">
              <div className="flex items-center gap-2 mb-1">
                <span>{severityIcons[fp.severity] || '●'}</span>
                <span className="font-medium text-gray-900">{fp.stage}</span>
                <span className="text-xs text-gray-500">[{fp.severity}]</span>
              </div>
              <p className="text-sm text-gray-700">
                <strong>Cause:</strong> {fp.cause}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                <strong>Fix:</strong> {fp.remediation}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Confidence */}
      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Explanation Confidence</span>
          <span className="text-lg font-bold text-gray-900">
            {(confidence.overall * 100).toFixed(0)}%
          </span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-gray-100">
          <div
            className="h-2 rounded-full bg-indigo-500"
            style={{ width: `${(confidence.overall * 100).toFixed(0)}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-gray-500">{confidence.interpretation}</p>
      </div>
    </div>
  );
}
