'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BrainCircuit, LayoutDashboard, BarChart3, GitBranch, MessageSquare, User } from 'lucide-react';

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

  return (
    <nav
      className={`sticky top-0 z-50 border-b backdrop-blur-xl ${
        isDashboard
          ? 'border-slate-800/50 bg-slate-950/80'
          : 'border-gray-200 bg-white/80'
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
            <BrainCircuit size={18} />
          </div>
          <span
            className={`text-sm font-bold ${
              isDashboard ? 'text-slate-100' : 'text-gray-900'
            }`}
          >
            AI Career Intelligence
          </span>
        </Link>

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
                      : 'bg-indigo-50 text-indigo-700'
                    : isDashboard
                    ? 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
