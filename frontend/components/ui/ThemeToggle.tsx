'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  if (!mounted) return <div className="h-8 w-8" />;

  const isDark = resolvedTheme === 'dark';

  return (
    <div className="flex items-center rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-0.5">
      <button
        onClick={() => setTheme('light')}
        className={`rounded-md p-1.5 transition-colors ${
          theme === 'light'
            ? 'bg-indigo-50 text-indigo-600 dark:bg-slate-800 dark:text-cyan-400'
            : 'text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300'
        }`}
        title="浅色模式"
      >
        <Sun size={14} />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={`rounded-md p-1.5 transition-colors ${
          theme === 'dark'
            ? 'bg-indigo-50 text-indigo-600 dark:bg-slate-800 dark:text-cyan-400'
            : 'text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300'
        }`}
        title="深色模式"
      >
        <Moon size={14} />
      </button>
      <button
        onClick={() => setTheme('system')}
        className={`rounded-md p-1.5 transition-colors ${
          theme === 'system'
            ? 'bg-indigo-50 text-indigo-600 dark:bg-slate-800 dark:text-cyan-400'
            : 'text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300'
        }`}
        title="跟随系统"
      >
        <Monitor size={14} />
      </button>
    </div>
  );
}
