'use client';

import { useState } from 'react';
import { useTheme } from 'next-themes';
import { useAuthStore } from '@/stores/authStore';
import { Moon, Sun, Monitor, Trash2, Shield } from 'lucide-react';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const logout = useAuthStore((s) => s.logout);
  const [clearConfirm, setClearConfirm] = useState(false);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-white">系统设置</h1>

      <div className="space-y-6">
        {/* Appearance */}
        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">外观</h2>
          <div className="flex gap-2">
            <ThemeButton
              active={theme === 'light'}
              onClick={() => setTheme('light')}
              icon={<Sun size={16} />}
              label="浅色"
            />
            <ThemeButton
              active={theme === 'dark'}
              onClick={() => setTheme('dark')}
              icon={<Moon size={16} />}
              label="深色"
            />
            <ThemeButton
              active={theme === 'system'}
              onClick={() => setTheme('system')}
              icon={<Monitor size={16} />}
              label="跟随系统"
            />
          </div>
        </section>

        {/* Privacy */}
        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">隐私与安全</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-200">
                <Shield size={16} />
                隐私级别
              </div>
              <select className="rounded-lg border px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white">
                <option>基础</option>
                <option>标准</option>
                <option>完整</option>
              </select>
            </div>
          </div>
        </section>

        {/* Data */}
        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">数据管理</h2>
          <div className="space-y-3">
            {!clearConfirm ? (
              <button
                onClick={() => setClearConfirm(true)}
                className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-100 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300"
              >
                <Trash2 size={14} />
                清除本地缓存
              </button>
            ) : (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  确定清除所有本地数据？
                </span>
                <button
                  onClick={() => {
                    localStorage.clear();
                    setClearConfirm(false);
                    logout();
                    window.location.href = '/';
                  }}
                  className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
                >
                  确认
                </button>
                <button
                  onClick={() => setClearConfirm(false)}
                  className="rounded-lg border px-3 py-1.5 text-sm dark:border-gray-600 dark:text-slate-200"
                >
                  取消
                </button>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function ThemeButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
        active
          ? 'border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-900/30 dark:bg-indigo-950/30 dark:text-indigo-300'
          : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
