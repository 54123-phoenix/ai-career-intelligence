'use client';

import { motion } from 'framer-motion';
import { SimulationHeatmap } from '@/components/charts/SimulationHeatmap';
import { SimulationGauge } from '@/components/charts/SimulationGauge';
import { GlassCard } from '@/components/ui/GlassCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { useI18n } from '@/lib/i18n';
import { Activity, CheckCircle, XCircle, Zap } from 'lucide-react';
import type { T010PipelineOutput } from '@/types/t010';

interface Props {
  data: T010PipelineOutput | null;
}

export function ActThreeSimulation({ data }: Props) {
  const { t } = useI18n();
  if (!data) return null;

  const feedback = data.simulation_feedback?.base_feedback;
  const rounds = feedback?.rounds.map((r) => ({
    round: r.round_id,
    probability: r.success_probability,
    success: r.success,
  }));

  const avgSuccess = feedback?.average_success_rate ?? 0;
  const totalRounds = feedback?.total_rounds ?? 0;
  const successCount = feedback?.successful_rounds ?? 0;

  return (
    <section className="space-y-4">
      <SectionHeader
        title={t('actThree.title')}
        subtitle={t('actThree.subtitle')}
        icon={<Activity size={18} />}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SimulationGauge
          value={avgSuccess}
          label={t('actThree.avgSuccessRate')}
          sublabel={`${successCount}/${totalRounds} rounds passed`}
          color={avgSuccess > 0.7 ? 'green' : avgSuccess > 0.4 ? 'cyan' : 'orange'}
        />

        <GlassCard glow="blue" delay={0.15} className="flex flex-col items-center justify-center py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/10 text-neon-blue">
            <Zap size={20} />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            <AnimatedNumber value={totalRounds} />
          </div>
          <div className="text-xs text-slate-400">{t('actThree.totalRounds')}</div>
        </GlassCard>

        <GlassCard glow="green" delay={0.2} className="flex flex-col items-center justify-center py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-neon-green">
            <CheckCircle size={20} />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            <AnimatedNumber value={successCount} />
          </div>
          <div className="text-xs text-slate-400">{t('actThree.passed')}</div>
        </GlassCard>

        <GlassCard glow="red" delay={0.25} className="flex flex-col items-center justify-center py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/10 text-neon-red">
            <XCircle size={20} />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            <AnimatedNumber value={totalRounds - successCount} />
          </div>
          <div className="text-xs text-slate-400">{t('actThree.failed')}</div>
        </GlassCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SimulationHeatmap
            rounds={rounds}
            aggregatedRisks={feedback?.aggregated_risks}
            title={t('actThree.heatmapTitle')}
          />
        </div>

        <div className="space-y-4">
          {/* Top risks */}
          {feedback && Object.keys(feedback.aggregated_risks).length > 0 && (
            <GlassCard glow="orange" delay={0.3}>
              <div className="mb-3 text-xs font-medium text-slate-400">{t('actThree.aggregatedRisks')}</div>
              <div className="space-y-2">
                {Object.entries(feedback.aggregated_risks)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([risk, val], i) => (
                    <motion.div
                      key={risk}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + i * 0.05 }}
                      className="flex items-center gap-2"
                    >
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-700/50">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${val * 100}%` }}
                          transition={{ duration: 1, delay: 0.5 + i * 0.05 }}
                          className={`h-full rounded-full ${
                            val > 0.6 ? 'bg-neon-red' : val > 0.3 ? 'bg-neon-orange' : 'bg-neon-green'
                          }`}
                        />
                      </div>
                      <span className="w-20 truncate text-right text-xs text-slate-400">{risk}</span>
                      <span className="w-10 text-right text-xs font-mono text-slate-300">
                        {(val * 100).toFixed(0)}%
                      </span>
                    </motion.div>
                  ))}
              </div>
            </GlassCard>
          )}

          {/* Top skill gaps */}
          {feedback && Object.keys(feedback.aggregated_skill_gaps).length > 0 && (
            <GlassCard glow="red" delay={0.4}>
              <div className="mb-3 text-xs font-medium text-slate-400">{t('actThree.skillGaps')}</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(feedback.aggregated_skill_gaps)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 8)
                  .map(([gap, val], i) => (
                    <motion.span
                      key={gap}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 + i * 0.04 }}
                      className="rounded-md bg-red-500/10 px-2 py-1 text-xs font-medium text-neon-red ring-1 ring-red-500/20"
                    >
                      {gap} ({(val * 100).toFixed(0)}%)
                    </motion.span>
                  ))}
              </div>
            </GlassCard>
          )}

          {/* Diversity */}
          {data.diversity_metric && (
            <GlassCard glow="purple" delay={0.5}>
              <div className="mb-2 text-xs font-medium text-slate-400">{t('actThree.strategyDiversity')}</div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-2xl font-bold text-slate-100">
                    <AnimatedNumber value={data.diversity_metric.strategy_diversity * 100} suffix="%" />
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {t('actThree.overfittingRisk')}: {(data.diversity_metric.overfitting_risk * 100).toFixed(0)}%
                  </div>
                </div>
                <div
                  className={`h-10 w-10 rounded-full ${
                    data.diversity_metric.overfitting_risk > 0.6
                      ? 'bg-red-500/10 text-neon-red'
                      : 'bg-emerald-500/10 text-neon-green'
                  } flex items-center justify-center text-lg font-bold`}
                >
                  {data.diversity_metric.overfitting_risk > 0.6 ? '!' : '✓'}
                </div>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </section>
  );
}
