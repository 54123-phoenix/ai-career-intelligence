'use client';

import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { StrategyComparisonData, ScoredStrategy } from '@/types/t008';
import { GlassCard } from '@/components/ui/GlassCard';

interface Props {
  data: StrategyComparisonData | null;
  strategies?: ScoredStrategy[];
  activeIndex?: number;
  onSelect?: (index: number) => void;
}

const STRATEGY_COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function StrategyRadar({ data, strategies, activeIndex = 0, onSelect }: Props) {
  const option = useMemo(() => {
    const dimensions = data?.dimensions ?? ['success_rate', 'match_degree', 'growth_cycle', 'skill_adaptability'];
    const indicator = dimensions.map((dim) => ({
      name: dim.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      max: 1,
    }));

    const seriesData =
      data?.strategies.map((s, i) => ({
        value: [s.success_rate, s.match_degree, s.growth_cycle, s.skill_adaptability],
        name: s.name,
        lineStyle: {
          color: STRATEGY_COLORS[i % STRATEGY_COLORS.length],
          width: i === activeIndex ? 3 : 1.5,
        },
        itemStyle: {
          color: STRATEGY_COLORS[i % STRATEGY_COLORS.length],
        },
        areaStyle: {
          color: STRATEGY_COLORS[i % STRATEGY_COLORS.length],
          opacity: i === activeIndex ? 0.2 : 0.05,
        },
      })) ?? [];

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15,23,42,0.95)',
        borderColor: 'rgba(148,163,184,0.15)',
        textStyle: { color: '#f1f5f9' },
      },
      legend: {
        data: data?.strategies.map((s) => s.name) ?? [],
        textStyle: { color: '#94a3b8', fontSize: 11 },
        bottom: 0,
        itemWidth: 14,
        itemHeight: 8,
      },
      radar: {
        indicator,
        center: ['50%', '45%'],
        radius: '60%',
        axisName: {
          color: '#94a3b8',
          fontSize: 11,
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(30,41,59,0.3)', 'rgba(30,41,59,0.5)'],
          },
        },
        splitLine: {
          lineStyle: { color: 'rgba(148,163,184,0.15)' },
        },
        axisLine: {
          lineStyle: { color: 'rgba(148,163,184,0.15)' },
        },
      },
      series: [
        {
          type: 'radar',
          data: seriesData,
          animationDuration: 1000,
          animationEasing: 'cubicOut',
        },
      ],
    };
  }, [data, activeIndex]);

  return (
    <GlassCard className="h-full" glow="blue">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Strategy Radar</h3>
        <span className="text-xs text-slate-500">Multi-dimension comparison</span>
      </div>
      <ReactECharts option={option} style={{ height: 320 }} opts={{ renderer: 'canvas' }} />
      {data && data.strategies.length > 1 && onSelect && (
        <div className="mt-2 flex flex-wrap gap-2">
          {data.strategies.map((s, i) => (
            <button
              key={s.name}
              onClick={() => onSelect(i)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                i === activeIndex
                  ? 'bg-slate-700 text-white shadow'
                  : 'bg-slate-800/60 text-slate-400 hover:bg-slate-700/60'
              }`}
              style={
                i === activeIndex
                  ? { borderLeft: `3px solid ${STRATEGY_COLORS[i % STRATEGY_COLORS.length]}` }
                  : {}
              }
            >
              {s.name} ({(s.overall * 100).toFixed(0)}%)
            </button>
          ))}
        </div>
      )}
    </GlassCard>
  );
}
