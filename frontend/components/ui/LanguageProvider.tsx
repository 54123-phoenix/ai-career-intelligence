'use client';

import { useState, useMemo, useEffect } from 'react';
import { I18nContext, makeT, type Language } from '@/lib/i18n';

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Language>('zh');

  // Persist language preference
  useEffect(() => {
    const saved = localStorage.getItem('aci-language') as Language | null;
    if (saved && (saved === 'zh' || saved === 'en')) {
      setLang(saved);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('aci-language', lang);
  }, [lang]);

  const t = useMemo(() => makeT(lang), [lang]);

  const value = useMemo(
    () => ({
      lang,
      setLang,
      t,
    }),
    [lang, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
