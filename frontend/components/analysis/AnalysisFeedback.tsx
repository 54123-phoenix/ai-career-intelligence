'use client';

import { useState } from 'react';
import { submitCareerFeedback } from '@/lib/api/career';

interface Props {
  analysisId: string;
}

export function AnalysisFeedback({ analysisId }: Props) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit() {
    if (!rating) return;
    setLoading(true);
    setMessage(null);
    try {
      await submitCareerFeedback({
        analysis_id: analysisId,
        rating,
        comments: comment,
      });
      setMessage('感谢您的反馈！');
      setRating(0);
      setComment('');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : '提交失败');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(null), 4000);
    }
  }

  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
      <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">分析反馈</h3>
      {message && (
        <div className="mb-3 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-900/30 dark:bg-green-950/30 dark:text-green-300">
          {message}
        </div>
      )}
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">评分：</span>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            className={`text-xl transition-colors ${
              star <= rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
            }`}
          >
            ★
          </button>
        ))}
      </div>
      <textarea
        className="mb-3 w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
        rows={2}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="您的建议或意见..."
      />
      <button
        onClick={handleSubmit}
        disabled={loading || !rating}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {loading ? '提交中...' : '提交反馈'}
      </button>
    </div>
  );
}
