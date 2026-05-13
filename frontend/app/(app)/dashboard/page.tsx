'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { useCareerStore } from '@/stores/careerStore';
import { getUserHistory, type UserHistoryItem } from '@/lib/api/user';
import {
  BarChart3,
  GitBranch,
  MessageSquare,
  Zap,
  TrendingUp,
  Award,
  Calendar,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const history = useCareerStore((s) => s.history);
  const [recentActivity, setRecentActivity] = useState<UserHistoryItem[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);

  useEffect(() => {
    getUserHistory({ limit: 5 })
      .then((res) => setRecentActivity(res.items))
      .catch(() => {})
      .finally(() => setActivityLoading(false));
  }, []);

  const skillCount = user?.skills?.length ?? 0;
  const analysisCount = history.length;

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <section>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          欢迎回来，{user?.name || '用户'} 👋
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          这里是您的职业发展仪表盘，查看分析结果、运行模拟或咨询 AI 助手。
        </p>
      </section>

      {/* Stats Grid */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<BarChart3 size={18} />}
          label="职业分析"
          value={analysisCount}
          sub="次已完成"
          color="indigo"
        />
        <StatCard
          icon={<Award size={18} />}
          label="技能标签"
          value={skillCount}
          sub="项已记录"
          color="emerald"
        />
        <StatCard
          icon={<TrendingUp size={18} />}
          label="职业目标"
          value={user?.career_goals?.length ?? 0}
          sub="个目标"
          color="amber"
        />
        <StatCard
          icon={<Calendar size={18} />}
          label="近期活动"
          value={recentActivity.length}
          sub="条记录"
          color="rose"
        />
      </section>

      {/* Quick Actions */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
          快捷入口
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <QuickActionCard
            href="/analysis"
            icon={<Sparkles size={20} />}
            title="职业分析"
            desc="解析画像、推荐岗位、生成策略"
            color="indigo"
          />
          <QuickActionCard
            href="/simulation"
            icon={<GitBranch size={20} />}
            title="职业模拟"
            desc="运行模拟、对比策略、评估路径"
            color="emerald"
          />
          <QuickActionCard
            href="/chat"
            icon={<MessageSquare size={20} />}
            title="AI 助手"
            desc="职业建议问答与策略讨论"
            color="amber"
          />
        </div>
      </section>

      {/* Recent Activity + Skills */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Activity */}
        <section className="rounded-xl border bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white">最近活动</h2>
            <Link
              href="/profile"
              className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              查看全部 <ArrowRight size={12} />
            </Link>
          </div>

          {activityLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-gray-100 dark:bg-slate-800" />
              ))}
            </div>
          ) : recentActivity.length === 0 ? (
            <p className="py-6 text-center text-sm text-gray-400 dark:text-gray-500">
              暂无活动记录，开始您的第一次职业分析吧
            </p>
          ) : (
            <div className="space-y-2">
              {recentActivity.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm dark:border-gray-700"
                >
                  <div className="flex items-center gap-2">
                    <ActivityIcon type={item.type} />
                    <span className="text-gray-900 dark:text-white">{item.title}</span>
                    <span className="text-xs text-gray-400">{item.description}</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(item.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Skills & Profile Summary */}
        <section className="rounded-xl border bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white">我的技能</h2>
            <Link
              href="/profile"
              className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              编辑资料 <ArrowRight size={12} />
            </Link>
          </div>

          {skillCount === 0 ? (
            <p className="py-6 text-center text-sm text-gray-400 dark:text-gray-500">
              尚未记录技能标签，前往用户中心添加
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {user?.skills?.map((skill) => (
                <span
                  key={skill}
                  className="rounded-lg bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}

          {user?.career_goals && user.career_goals.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                职业目标
              </h3>
              <div className="flex flex-wrap gap-2">
                {user.career_goals.map((goal) => (
                  <span
                    key={goal}
                    className="rounded-lg bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300"
                  >
                    {goal}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  sub: string;
  color: 'indigo' | 'emerald' | 'amber' | 'rose';
}) {
  const colorMap = {
    indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300',
    emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300',
    rose: 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300',
  };

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-slate-900">
      <div className="mb-2 flex items-center gap-2">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${colorMap[color]}`}>
          {icon}
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">{value}</span>
        <span className="text-xs text-gray-500 dark:text-gray-400">{sub}</span>
      </div>
    </div>
  );
}

function QuickActionCard({
  href,
  icon,
  title,
  desc,
  color,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  desc: string;
  color: 'indigo' | 'emerald' | 'amber';
}) {
  const colorMap = {
    indigo:
      'hover:border-indigo-300 hover:bg-indigo-50/50 dark:hover:border-indigo-800 dark:hover:bg-indigo-950/20',
    emerald:
      'hover:border-emerald-300 hover:bg-emerald-50/50 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20',
    amber:
      'hover:border-amber-300 hover:bg-amber-50/50 dark:hover:border-amber-800 dark:hover:bg-amber-950/20',
  };

  return (
    <Link
      href={href}
      className={`group flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm transition-colors dark:border-gray-700 dark:bg-slate-900 ${colorMap[color]}`}
    >
      <div className="mt-0.5 text-gray-500 transition-colors group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white">
        {icon}
      </div>
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
        <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{desc}</p>
      </div>
      <ArrowRight
        size={16}
        className="ml-auto mt-1 text-gray-300 transition-colors group-hover:text-gray-500 dark:text-gray-600 dark:group-hover:text-gray-300"
      />
    </Link>
  );
}

function ActivityIcon({ type }: { type: UserHistoryItem['type'] }) {
  const map: Record<string, { icon: React.ReactNode; bg: string }> = {
    analysis: {
      icon: <BarChart3 size={12} className="text-indigo-600 dark:text-indigo-400" />,
      bg: 'bg-indigo-50 dark:bg-indigo-950/30',
    },
    simulation: {
      icon: <GitBranch size={12} className="text-emerald-600 dark:text-emerald-400" />,
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    },
    chat: {
      icon: <MessageSquare size={12} className="text-amber-600 dark:text-amber-400" />,
      bg: 'bg-amber-50 dark:bg-amber-950/30',
    },
    profile_update: {
      icon: <Zap size={12} className="text-rose-600 dark:text-rose-400" />,
      bg: 'bg-rose-50 dark:bg-rose-950/30',
    },
  };
  const config = map[type] || map.profile_update;
  return (
    <div className={`flex h-6 w-6 items-center justify-center rounded-full ${config.bg}`}>
      {config.icon}
    </div>
  );
}
