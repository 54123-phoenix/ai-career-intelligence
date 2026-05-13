/** Simple i18n system for AI Career Intelligence Dashboard */

import { createContext, useContext, useCallback, useState } from 'react';
import { zh, type Zh } from './locales/zh';
import { en, type En } from './locales/en';

export type Language = 'zh' | 'en';
export type Dictionary = Zh | En;

const dictionaries: Record<Language, Dictionary> = { zh, en };

interface I18nContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue>({
  lang: 'zh',
  setLang: () => {},
  t: (key: string) => key,
});

export function useI18n() {
  return useContext(I18nContext);
}

/** Get nested value from dictionary by dot-notation key */
function getDictValue(dict: Dictionary, key: string): string | string[] | Record<string, string> | undefined {
  const parts = key.split('.');
  let current: unknown = dict;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return current as string | string[] | Record<string, string> | undefined;
}

/** Create translate function for given language */
export function makeT(lang: Language) {
  const dict = dictionaries[lang];
  return (key: string, vars?: Record<string, string | number>): string => {
    const value = getDictValue(dict, key);
    let text: string;

    if (typeof value === 'string') {
      text = value;
    } else if (Array.isArray(value)) {
      text = value[0] ?? key;
    } else if (typeof value === 'object' && value !== null) {
      text = Object.values(value)[0] ?? key;
    } else {
      text = key;
    }

    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
      });
    }

    return text;
  };
}

/** Hook that returns translate function bound to current language */
export function useT() {
  const { lang } = useContext(I18nContext);
  return useCallback(
    (key: string, vars?: Record<string, string | number>) => makeT(lang)(key, vars),
    [lang]
  );
}
