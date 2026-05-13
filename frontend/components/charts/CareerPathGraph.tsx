'use client';

import { useMemo, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { VisualizationGraph } from '@/types/t008';
import { GlassCard } from '@/components/ui/GlassCard';

interface Props {
  data: VisualizationGraph | null;
  onNodeClick?: (nodeName: string) => void;
  activeStrategy?: string;
}

const LEVEL_COLORS: Record<string, string> = {
  beginner: '#06b6d4',
  intermediate: '#10b981',
  advanced: '#f59e0b',
  expert: '#ef4444',
};

export function CareerPathGraph({ data, onNodeClick, activeStrategy }: Props) {
  const option = useMemo(() => {
    if (!data || !data.skill_nodes.length) {
      return {
        backgroundColor: 'transparent',
        title: {
          text: 'No path data',
          left: 'center',
          top: 'center',
          textStyle: { color: '#64748b', fontSize: 14 },
        },
      };
    }

    const nodes = data.skill_nodes.map((node) => ({
      id: node.skill_name,
      name: node.skill_name,
      value: node.estimated_hours || 10,
      symbolSize: node.level === 'expert' ? 50 : node.level === 'advanced' ? 40 : node.level === 'intermediate' ? 32 : 26,
      itemStyle: {
        color: LEVEL_COLORS[node.level] || '#64748b',
        shadowBlur: 20,
        shadowColor: LEVEL_COLORS[node.level] || '#64748b',
      },
      label: {
        show: true,
        color: '#e2e8f0',
        fontSize: 11,
        fontWeight: 'bold',
      },
      category: node.level,
    }));

    const edges = data.skill_edges.map(([from, to]) => ({
      source: from,
      target: to,
      lineStyle: {
        color: 'rgba(148,163,184,0.3)',
        width: 1.5,
        curveness: 0.2,
      },
    }));

    // Add primary path edges with glowing effect
    if (data.primary_path.length > 1) {
      for (let i = 0; i < data.primary_path.length - 1; i++) {
        const from = data.primary_path[i];
        const to = data.primary_path[i + 1];
        const existing = edges.find((e) => e.source === from && e.target === to);
        if (existing) {
          existing.lineStyle = {
            color: '#06b6d4',
            width: 3,
            shadowBlur: 10,
            shadowColor: '#06b6d4',
            curveness: 0.2,
          } as any;
        } else {
          edges.push({
            source: from,
            target: to,
            lineStyle: {
              color: '#06b6d4',
              width: 3,
              curveness: 0.2,
            } as any,
          });
        }
      }
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15,23,42,0.95)',
        borderColor: 'rgba(148,163,184,0.15)',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const node = data.skill_nodes.find((n) => n.skill_name === params.name);
            if (!node) return params.name;
            return `
              <div style="font-weight:bold;margin-bottom:4px">${node.skill_name}</div>
              <div style="color:#94a3b8;font-size:12px">Level: <span style="color:${LEVEL_COLORS[node.level] || '#fff'}">${node.level}</span></div>
              <div style="color:#94a3b8;font-size:12px">Est. hours: ${node.estimated_hours}h</div>
              ${node.dependencies.length ? `<div style="color:#94a3b8;font-size:12px">Requires: ${node.dependencies.join(', ')}</div>` : ''}
            `;
          }
          return `${params.data.source} → ${params.data.target}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: nodes,
          edges,
          roam: true,
          draggable: true,
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 4 },
          },
          force: {
            repulsion: 300,
            edgeLength: 100,
            gravity: 0.1,
          },
          animationDuration: 1500,
          animationEasingUpdate: 'quinticInOut',
        },
      ],
    };
  }, [data, activeStrategy]);

  const onEvents = useCallback(
    () => ({
      click: (params: any) => {
        if (params.dataType === 'node' && onNodeClick) {
          onNodeClick(params.name);
        }
      },
    }),
    [onNodeClick]
  );

  return (
    <GlassCard className="h-full min-h-[400px]" glow="cyan">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Career Path Network</h3>
        <div className="flex gap-3 text-xs">
          {Object.entries(LEVEL_COLORS).map(([level, color]) => (
            <span key={level} className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-slate-400 capitalize">{level}</span>
            </span>
          ))}
        </div>
      </div>
      <ReactECharts
        option={option}
        style={{ height: 360 }}
        onEvents={onEvents()}
        opts={{ renderer: 'canvas' }}
      />
    </GlassCard>
  );
}
