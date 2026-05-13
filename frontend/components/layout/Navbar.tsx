'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import {
  BrainCircuit,
  LayoutDashboard,
  BarChart3,
  GitBranch,
  MessageSquare,
  User,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { useAuthStore } from '@/stores/authStore';

const navItems = [
  { href: '/dashboard', label: '仪表盘', icon: <LayoutDashboard size={16} /> },
  { href: '/analysis', label: '职业分析', icon: <BarChart3 size={16} /> },
  { href: '/simulation', label: '职业模拟', icon: <GitBranch size={16} /> },
  { href: '/chat', label: 'AI助手', icon: <MessageSquare size={16} /> },
  { href: '/profile', label: '用户中心', icon: <User size={16} /> },
];

export function Navbar() {
  const pathname = usePathname();
  const isDashboard = pathname === '/dashboard';
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-50 border-b backdrop-blur-xl ${
        isDashboard
          ? 'border-slate-800/50 bg-slate-950/80 dark:bg-slate-950/80'
          : 'border-gray-200 bg-white/80 dark:border-slate-800 dark:bg-slate-950/80'
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
            <BrainCircuit size={18} />
          </div>
          <span
            className={`text-sm font-bold ${
              isDashboard ? 'text-slate-100' : 'text-gray-900 dark:text-slate-100'
            }`}
          >
            AI Career Intelligence
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname?.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? isDashboard
                        ? 'bg-slate-800 text-slate-100'
                        : 'bg-indigo-50 text-indigo-700 dark:bg-slate-800 dark:text-cyan-400'
                      : isDashboard
                      ? 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200'
                  }`}
                >
                  {item.icon}
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="ml-2 flex items-center gap-2 border-l border-gray-200 pl-2 dark:border-slate-700">
            <ThemeToggle />

            {/* User dropdown */}
            {user && (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className={`flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium transition-colors ${
                    isDashboard
                      ? 'text-slate-300 hover:bg-slate-800'
                      : 'text-gray-700 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'
                  }`}
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
                    <User size={14} />
                  </div>
                  <span className="hidden sm:inline">{user.name || user.email}</span>
                  <ChevronDown size={14} />
                </button>

                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-44 rounded-lg border bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900">
                    <Link
                      href="/profile"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-slate-200 dark:hover:bg-slate-800"
                    >
                      <User size={14} />
                      用户中心
                    </Link>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                      }}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                    >
                      <LogOut size={14} />
                      退出登录
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
