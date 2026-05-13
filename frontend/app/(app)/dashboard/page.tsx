/** @deprecated — Dashboard 旧版页面，保留向后兼容。将在 Phase 6 重构为业务概览仪表盘。 */
'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ActOneInput } from '@/components/dashboard/ActOneInput';
import { ActTwoStrategy } from '@/components/dashboard/ActTwoStrategy';
import { ActThreeSimulation } from '@/components/dashboard/ActThreeSimulation';
import { NodeDetailDrawer } from '@/components/dashboard/NodeDetailDrawer';
import { GlassCard } from '@/components/ui/GlassCard';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { AnalysisLoading } from '@/components/ui/AnalysisLoading';
import { TechBackground } from '@/components/ui/TechBackground';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';
import { analyzeCareer } from '@/lib/career-api';
import { useI18n } from '@/lib/i18n';
import type { T010PipelineOutput } from '@/types/t010';
import {
  BrainCircuit,
  ChevronDown,
  Play,
  RotateCcw,
  Zap,
  Shield,
  Clock,
  Cpu,
} from 'lucide-react';

const SAMPLE_DATASET: Record<string, unknown>[] = [
  {
    job_title: 'Senior Backend Engineer',
    required_skills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Kubernetes'],
    optional_skills: ['AWS', 'Terraform', 'GraphQL'],
    growth_path: ['Junior Backend', 'Backend Engineer', 'Senior Backend', 'Staff Engineer'],
    level: '高级',
    salary_range: [400, 650],
    location: '北京',
    industry: '互联网',
    source: 'sample',
  },
  {
    job_title: 'Machine Learning Engineer',
    required_skills: ['Python', 'PyTorch', 'TensorFlow', 'Machine Learning', 'Deep Learning'],
    optional_skills: ['Kubernetes', 'MLOps', 'NLP'],
    growth_path: ['Data Analyst', 'ML Engineer', 'Senior MLE', 'ML Architect'],
    level: '高级',
    salary_range: [500, 800],
    location: '上海',
    industry: '人工智能',
    source: 'sample',
  },
  {
    job_title: 'Frontend Tech Lead',
    required_skills: ['TypeScript', 'React', 'Next.js', 'CSS', 'System Design'],
    optional_skills: ['GraphQL', 'Webpack', 'React Native'],
    growth_path: ['Frontend Developer', 'Senior Frontend', 'Tech Lead', 'Frontend Architect'],
    level: '高级',
    salary_range: [450, 700],
    location: '深圳',
    industry: '互联网',
    source: 'sample',
  },
];

export default function DashboardPage() {
  const { t } = useI18n();
  const [data, setData] = useState<T010PipelineOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userInput, setUserInput] = useState(
    '目标成为高级后端工程师，掌握 Python、FastAPI、PostgreSQL，有3年经验，本科，期望在北京工作'
  );
  const [activeStrategyIndex, setActiveStrategyIndex] = useState(0);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [demoStage, setDemoStage] = useState(0);
  const [dataSource, setDataSource] = useState<'api' | 'mock' | null>(null);

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);
    setDemoStage(0);
    setDataSource(null);
    try {
      const result = await analyzeCareer({
        user_id: 'demo-user',
        user_input: userInput,
        career_dataset: SAMPLE_DATASET,
        privacy_level: 'basic',
      });
      setData(result.data);
      setDataSource(result.source);
      setDemoStage(1);
      setTimeout(() => setDemoStage(2), 800);
      setTimeout(() => setDemoStage(3), 1600);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [userInput]);

  const handleReset = useCallback(() => {
    setData(null);
    setError(null);
    setDemoStage(0);
    setActiveStrategyIndex(0);
    setSelectedNode(null);
    setDataSource(null);
  }, []);

  const statusColor =
    data?.status === 'success'
      ? 'text-neon-green'
      : data?.status === 'partial'
      ? 'text-neon-orange'
      : 'text-neon-red';

  return (
    <div className="min-h-screen bg-slate-950 pb-20">
      <TechBackground />

      {/* Dashboard Toolbar */}
      <div className="border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            {data && (
              <div className="hidden items-center gap-3 text-xs sm:flex">
                <span className={`flex items-center gap-1 font-medium ${statusColor}`}>
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                  {data.status}
                </span>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400">
                  <Clock size={12} className="mr-1 inline" />
                  {data.elapsed_ms.toFixed(0)}ms
                </span>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400">
                  <Zap size={12} className="mr-1 inline" />
                  {data.strategy_candidates.length} {t('status.candidates')}
                </span>
                {dataSource === 'mock' && (
                  <>
                    <span className="text-slate-500">|</span>
                    <span className="flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-400 ring-1 ring-amber-500/20">
                      <Cpu size={10} />
                      {t('nav.demoBadge')}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            {data ? (
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 rounded-lg border border-slate-700/50 bg-slate-900/60 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800"
              >
                <RotateCcw size={12} />
                {t('nav.reset')}
              </button>
            ) : (
              <button
                onClick={handleRun}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-neon-cyan to-neon-blue px-4 py-1.5 text-xs font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:shadow-cyan-500/40 disabled:opacity-50"
              >
                <Play size={12} />
                {loading ? t('nav.running') : t('nav.quickRun')}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 mx-auto max-w-7xl space-y-8 px-4 pt-6">
        {/* Hero */}
        {!data && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="py-12 text-center"
          >
            <motion.div
              className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-neon-cyan/20 to-neon-blue/20 ring-1 ring-cyan-500/20"
              animate={{
                boxShadow: [
                  '0 0 0px rgba(6,182,212,0)',
                  '0 0 30px rgba(6,182,212,0.2)',
                  '0 0 0px rgba(6,182,212,0)',
                ],
              }}
              transition={{ repeat: Infinity, duration: 3 }}
            >
              <BrainCircuit size={32} className="text-neon-cyan" />
            </motion.div>
            <h2 className="mb-2 text-3xl font-bold text-gradient-cyan">
              {t('hero.title')}
            </h2>
            <p className="mx-auto max-w-xl text-sm text-slate-400">
              {t('hero.description')}
            </p>
            <div className="mt-6 flex justify-center gap-2">
              <button
                onClick={handleRun}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-blue px-6 py-3 text-sm font-bold text-white shadow-xl shadow-cyan-500/20 transition-all hover:scale-105 hover:shadow-cyan-500/40"
              >
                <Play size={16} />
                {t('hero.startBtn')}
              </button>
            </div>
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="mt-12 text-slate-600"
            >
              <ChevronDown size={20} className="mx-auto" />
            </motion.div>
          </motion.div>
        )}

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <GlassCard glow="red" className="border-red-500/30 bg-red-500/5">
                <div className="text-sm text-red-300">{error}</div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Pipeline Loading */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="flex min-h-[60vh] items-center justify-center py-8"
            >
              <div className="w-full">
                <AnalysisLoading />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Act I */}
        {demoStage >= 1 && (
          <ActOneInput
            userInput={userInput}
            setUserInput={setUserInput}
            onRun={handleRun}
            loading={loading}
            profile={data?.user_profile ?? null}
          />
        )}

        {/* Divider */}
        {demoStage >= 2 && (
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.8 }}
            className="h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent"
          />
        )}

        {/* Act II */}
        {demoStage >= 2 && (
          <ActTwoStrategy
            data={data}
            activeStrategyIndex={activeStrategyIndex}
            setActiveStrategyIndex={setActiveStrategyIndex}
            onNodeClick={setSelectedNode}
          />
        )}

        {/* Divider */}
        {demoStage >= 3 && (
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.8 }}
            className="h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent"
          />
        )}

        {/* Act III */}
        {demoStage >= 3 && <ActThreeSimulation data={data} />}

        {/* Footer stats */}
        {data && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="border-t border-slate-800/50 pt-6 text-center"
          >
            <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500">
              <span>
                {t('status.generated')}: <span className="font-mono text-slate-400">{new Date(data.generated_at).toLocaleTimeString()}</span>
              </span>
              <span>
                {t('status.elapsed')}: <span className="font-mono text-slate-400">{data.elapsed_ms.toFixed(0)}ms</span>
              </span>
              {dataSource === 'mock' && (
                <span className="rounded bg-amber-500/10 px-2 py-0.5 text-amber-400 ring-1 ring-amber-500/20">
                  {t('status.demoMode')}
                </span>
              )}
            </div>
          </motion.div>
        )}
      </main>

      {/* Node Detail Modal */}
      <NodeDetailDrawer nodeName={selectedNode} data={data} onClose={() => setSelectedNode(null)} />
    </div>
  );
}
