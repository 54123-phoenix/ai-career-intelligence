'use client';

import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { GlassCard } from '@/components/ui/GlassCard';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';

interface Props {
  value: number; // 0-1
  label: string;
  sublabel?: string;
  color?: 'cyan' | 'green' | 'orange' | 'red';
}

const COLOR_MAP = {
  cyan: { start: '#06b6d4', end: '#3b82f6' },
  green: { start: '#10b981', end: '#059669' },
  orange: { start: '#f59e0b', end: '#d97706' },
  red: { start: '#ef4444', end: '#dc2626' },
};

export function SimulationGauge({ value, label, sublabel, color = 'cyan' }: Props) {
  const colors = COLOR_MAP[color];
  const pct = Math.round(value * 100);

  const option = useMemo(() => {
    return {
      backgroundColor: 'transparent',
      series: [
        {
          type: 'gauge',
          startAngle: 200,
          endAngle: -20,
          radius: '90%',
          min: 0,
          max: 100,
          splitNumber: 10,
          itemStyle: {
            color: colors.start,
            shadowColor: colors.start + '80',
            shadowBlur: 15,
          },
          progress: {
            show: true,
            roundCap: true,
            width: 12,
          },
          pointer: {
            show: false,
          },
          axisLine: {
            roundCap: true,
            lineStyle: { width: 12, color: [[1, 'rgba(30,41,59,0.8)']] },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          title: { show: false },
          detail: { show: false },
          data: [{ value: pct }],
          animationDuration: 1500,
          animationEasing: 'cubicOut',
        },
      ],
    };
  }, [pct, colors]);

  return (
    <GlassCard className="flex flex-col items-center justify-center py-6" glow={color}>
      <div className="relative h-36 w-36">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} />
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <AnimatedNumber value={pct} suffix="%" className="text-2xl font-bold text-slate-100" />
        </div>
      </div>
      <div className="mt-2 text-center">
        <div className="text-sm font-medium text-slate-200">{label}</div>
        {sublabel && <div className="text-xs text-slate-500">{sublabel}</div>}
      </div>
    </GlassCard>
  );
}
