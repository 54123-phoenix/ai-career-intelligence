import Link from 'next/link';
import { BrainCircuit, BarChart3, GitBranch, MessageSquare, Shield, Zap } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-slate-950 dark:text-slate-100">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-gray-200 px-4 py-24 dark:border-slate-800">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:border-indigo-900/30 dark:bg-indigo-950/30 dark:text-indigo-300">
            <Zap size={12} />
            AI 驱动的职业决策平台
          </div>
          <h1 className="mb-4 text-4xl font-extrabold tracking-tight sm:text-5xl">
            让 AI 为您的职业
            <br />
            <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              做出更聪明的选择
            </span>
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-gray-500 dark:text-slate-400">
            结合多 Agent 智能分析、职业路径模拟与实时对话助手，
            帮助您精准定位发展方向、评估策略可行性、制定可执行的成长计划。
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/register"
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
            >
              免费开始
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              登录账户
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-12 text-center text-2xl font-bold">核心能力</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<BarChart3 size={20} />}
              title="职业分析引擎"
              desc="解析职业画像、推荐匹配岗位、生成发展策略并模拟验证"
            />
            <FeatureCard
              icon={<GitBranch size={20} />}
              title="职业模拟与演化"
              desc="模拟不同职业路径上的成长、晋升与技能变化，对比策略优劣"
            />
            <FeatureCard
              icon={<MessageSquare size={20} />}
              title="AI 职业助手"
              desc="提供职业建议问答、策略讨论与路径规划支持"
            />
            <FeatureCard
              icon={<BrainCircuit size={20} />}
              title="多 Agent 协同"
              desc="解析、检索、评审、架构、模拟多阶段智能协作"
            />
            <FeatureCard
              icon={<Shield size={20} />}
              title="隐私可控"
              desc="支持基础、标准、深度三级隐私模式，数据安全可控"
            />
            <FeatureCard
              icon={<Zap size={20} />}
              title="实时反馈"
              desc="流式对话响应，即时获取职业建议与策略调整"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-4 py-8 dark:border-slate-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-slate-400">
            <BrainCircuit size={16} />
            <span>AI Career Intelligence System</span>
          </div>
          <div className="text-xs text-gray-400 dark:text-slate-500">
            © 2026 All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-colors dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950/30 dark:text-indigo-400">
        {icon}
      </div>
      <h3 className="mb-1 font-semibold text-gray-900 dark:text-white">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-slate-400">{desc}</p>
    </div>
  );
}
