'use client';

import { useI18n } from '@/lib/i18n';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();

  return (
    <button
      onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
      className="flex items-center gap-1.5 rounded-lg border border-slate-700/50 bg-slate-900/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800"
      title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      <Globe size={13} />
      <span className="uppercase tracking-wide">{lang === 'zh' ? 'EN' : '中'}</span>
    </button>
  );
}
