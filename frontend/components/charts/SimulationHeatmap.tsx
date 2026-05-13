'use client';

import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { GlassCard } from '@/components/ui/GlassCard';

interface HeatmapCell {
  x: string;
  y: string;
  value: number;
}

interface Props {
  rounds?: Array<{ round: number; probability: number; success: boolean }>;
  aggregatedRisks?: Record<string, number>;
  title?: string;
}

export function SimulationHeatmap({ rounds, aggregatedRisks, title = 'Simulation Heatmap' }: Props) {
  const option = useMemo(() => {
    // Build data for heatmap: rounds x metrics
    const metrics = ['Success Prob', 'Risk Exposure', 'Skill Gap'];
    const roundsData = rounds ?? [
      { round: 1, probability: 0.72, success: true },
      { round: 2, probability: 0.68, success: true },
      { round: 3, probability: 0.55, success: false },
      { round: 4, probability: 0.81, success: true },
      { round: 5, probability: 0.76, success: true },
    ];

    const data: [number, number, number][] = [];
    roundsData.forEach((r, roundIdx) => {
      data.push([roundIdx, 0, r.probability]);
      const riskVal = aggregatedRisks ? Object.values(aggregatedRisks)[roundIdx % Object.values(aggregatedRisks).length] || 0.3 : 0.3 + Math.random() * 0.4;
      data.push([roundIdx, 1, riskVal]);
      data.push([roundIdx, 2, Math.max(0, 1 - r.probability - riskVal * 0.5)]);
    });

    return {
      backgroundColor: 'transparent',
      tooltip: {
        position: 'top',
        backgroundColor: 'rgba(15,23,42,0.95)',
        borderColor: 'rgba(148,163,184,0.15)',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => {
          const roundLabel = `Round ${params.value[0] + 1}`;
          const metric = metrics[params.value[1]];
          const val = (params.value[2] * 100).toFixed(0);
          return `<div style="font-weight:bold">${roundLabel}</div><div style="color:#94a3b8">${metric}: ${val}%</div>`;
        },
      },
      grid: {
        top: 10,
        bottom: 30,
        left: 80,
        right: 10,
      },
      xAxis: {
        type: 'category',
        data: roundsData.map((_, i) => `R${i + 1}`),
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
        splitArea: { show: false },
      },
      yAxis: {
        type: 'category',
        data: metrics,
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
        splitArea: { show: false },
      },
      visualMap: {
        min: 0,
        max: 1,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        itemWidth: 12,
        itemHeight: 80,
        inRange: {
          color: ['#0f172a', '#1e3a5f', '#0ea5e9', '#06b6d4', '#10b981'],
        },
        textStyle: { color: '#94a3b8', fontSize: 10 },
      },
      series: [
        {
          type: 'heatmap',
          data,
          label: {
            show: true,
            formatter: (p: any) => `${(p.value[2] * 100).toFixed(0)}%`,
            color: '#e2e8f0',
            fontSize: 10,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 15,
              shadowColor: 'rgba(6,182,212,0.5)',
            },
          },
          animationDuration: 1000,
        },
      ],
    };
  }, [rounds, aggregatedRisks]);

  return (
    <GlassCard className="h-full" glow="green">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        <span className="text-xs text-slate-500">Round × Metric</span>
      </div>
      <ReactECharts option={option} style={{ height: 240 }} opts={{ renderer: 'canvas' }} />
    </GlassCard>
  );
}
