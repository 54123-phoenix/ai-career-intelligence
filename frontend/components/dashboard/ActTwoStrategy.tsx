'use client';

import { motion } from 'framer-motion';
import { StrategyRadar } from '@/components/charts/StrategyRadar';
import { CareerPathGraph } from '@/components/charts/CareerPathGraph';
import { GlassCard } from '@/components/ui/GlassCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { useI18n } from '@/lib/i18n';
import { Target, TrendingUp, AlertTriangle } from 'lucide-react';
import type { T010PipelineOutput } from '@/types/t010';
import type { ScoredStrategyV2 } from '@/types/t009';

interface Props {
  data: T010PipelineOutput | null;
  activeStrategyIndex: number;
  setActiveStrategyIndex: (i: number) => void;
  onNodeClick: (name: string) => void;
}

export function ActTwoStrategy({ data, activeStrategyIndex, setActiveStrategyIndex, onNodeClick }: Props) {
  const { t } = useI18n();
  if (!data) return null;

  const strategies = data.strategy_list;
  const activeStrategy: ScoredStrategyV2 | undefined = strategies[activeStrategyIndex];

  const radarData =
    strategies.length > 0
      ? {
          strategies: strategies.map((s) => ({
            name: s.strategy.strategy_name,
            overall: s.overall_score,
            success_rate: s.scores.success_rate ?? 0.7,
            match_degree: s.scores.match_degree ?? 0.7,
            growth_cycle: s.scores.growth_cycle ?? 0.7,
            skill_adaptability: s.scores.skill_adaptability ?? 0.7,
            rank: s.rank,
          })),
          dimensions: ['success_rate', 'match_degree', 'growth_cycle', 'skill_adaptability'],
        }
      : null;

  return (
    <section className="space-y-4">
      <SectionHeader
        title={t('actTwo.title')}
        subtitle={t('actTwo.subtitle')}
        icon={<Target size={18} />}
      />

      <div className="grid gap-4 lg:grid-cols-5">
        {/* Left: Strategy list + radar */}
        <div className="space-y-4 lg:col-span-2">
          <StrategyRadar
            data={radarData}
            activeIndex={activeStrategyIndex}
            onSelect={setActiveStrategyIndex}
          />

          <GlassCard glow="blue" delay={0.2}>
            <div className="mb-3 text-xs font-medium text-slate-400">{t('actTwo.topStrategies')}</div>
            <div className="space-y-2">
              {strategies.slice(0, 4).map((s, i) => (
                <motion.button
                  key={s.strategy.strategy_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.08 }}
                  onClick={() => setActiveStrategyIndex(i)}
                  className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left transition-all ${
                    i === activeStrategyIndex
                      ? 'border-cyan-500/30 bg-cyan-500/10'
                      : 'border-slate-700/30 bg-slate-800/30 hover:bg-slate-700/30'
                  }`}
                >
                  <div>
                    <div className="text-sm font-medium text-slate-200 capitalize">
                      {s.strategy.strategy_name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {s.off_path && <span className="mr-1 text-orange-400">⚠ off-path</span>}
                      {s.rationale.slice(0, 40)}...
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${i === 0 ? 'text-neon-cyan' : 'text-slate-300'}`}>
                      <AnimatedNumber value={s.overall_score * 100} suffix="%" decimals={0} />
                    </div>
                    <div className="text-[10px] text-slate-500">Rank #{s.rank}</div>
                  </div>
                </motion.button>
              ))}
            </div>
          </GlassCard>

          {/* Dynamic weights */}
          {data.dynamic_weights && (
            <GlassCard glow="purple" delay={0.4}>
              <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-400">
                <TrendingUp size={14} />
                {t('actTwo.rlWeights')} — {t('actTwo.rlIteration')} {data.dynamic_weights.iteration}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.dynamic_weights.weights).map(([dim, w]) => (
                  <div key={dim} className="rounded-md bg-slate-800/50 px-2 py-1.5">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">{dim}</div>
                    <div className="text-sm font-mono font-bold text-slate-200">{(w * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        {/* Right: Career path graph */}
        <div className="lg:col-span-3">
          <CareerPathGraph
            data={data.visualization_data}
            onNodeClick={onNodeClick}
            activeStrategy={activeStrategy?.strategy.strategy_name}
          />
        </div>
      </div>

      {/* Off-path warnings */}
      {data.off_path_flags.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-3 md:grid-cols-2 lg:grid-cols-3"
        >
          {data.off_path_flags.map((flag, i) => (
            <GlassCard key={i} glow="orange" delay={0.5 + i * 0.1}>
              <div className="flex items-start gap-2">
                <AlertTriangle size={16} className="mt-0.5 shrink-0 text-neon-orange" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200">{flag.flag_type}</span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                        flag.severity === 'high'
                          ? 'bg-red-500/20 text-red-400'
                          : flag.severity === 'medium'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {t(`actTwo.severity.${flag.severity}`)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{flag.description}</p>
                  {flag.recommendation && (
                    <p className="mt-1 text-xs text-neon-cyan">→ {flag.recommendation}</p>
                  )}
                </div>
              </div>
            </GlassCard>
          ))}
        </motion.div>
      )}
    </section>
  );
}
