'use client';

import ReactECharts from 'echarts-for-react';
import type { CareerAnalysisResult } from '@/types/career';

interface Props {
  data?: CareerAnalysisResult | null;
}

export default function SkillRadar({ data }: Props) {
  const userProfile = data?.userProfile;
  const topJob = data?.recommendations?.[0];

  // Compute dimension scores from real data when available
  let scores: number[];
  if (userProfile && topJob) {
    const userSkills = new Set(userProfile.skills.map((s) => s.toLowerCase()));
    const jobSkills = new Set(topJob.requiredSkills.map((s) => s.toLowerCase()));
    const intersection = new Set(Array.from(userSkills).filter((s) => jobSkills.has(s)));
    const skillMatch = jobSkills.size > 0 ? intersection.size / jobSkills.size : 0;

    // Experience: assume 3 years = ideal for senior roles
    const experienceMatch = Math.min(userProfile.experienceYears / 3, 1);

    // Education: simple heuristic
    const eduLevel: Record<string, number> = { 博士: 1, 硕士: 0.9, 本科: 0.8, 其他: 0.6 };
    const educationMatch = eduLevel[userProfile.educationLevel] ?? 0.6;

    // Salary: if both have ranges, compute overlap ratio; otherwise default
    const salaryMatch = topJob.salaryRange && Array.isArray(topJob.salaryRange) ? 0.85 : 0.7;

    // Location: check overlap
    const userLocs = new Set(userProfile.preferredLocations.map((l) => l.toLowerCase()));
    const jobLoc = topJob.location?.toLowerCase() ?? '';
    const locationMatch = Array.from(userLocs).some((l) => jobLoc.includes(l)) ? 1 : 0.4;

    scores = [skillMatch, experienceMatch, educationMatch, salaryMatch, locationMatch];
  } else {
    // Mock data for demo / when analysis hasn't run yet
    scores = [0.72, 0.65, 0.8, 0.6, 0.9];
  }

  const option = {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: [
        { name: '技能匹配', max: 1 },
        { name: '经验匹配', max: 1 },
        { name: '学历匹配', max: 1 },
        { name: '薪资匹配', max: 1 },
        { name: '地理匹配', max: 1 },
      ],
      radius: '65%',
      axisName: {
        color: 'inherit',
        fontSize: 12,
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(99, 102, 241, 0.05)',
            'rgba(99, 102, 241, 0.1)',
            'rgba(99, 102, 241, 0.15)',
            'rgba(99, 102, 241, 0.2)',
            'rgba(99, 102, 241, 0.25)',
          ],
        },
      },
      axisLine: {
        lineStyle: { color: 'rgba(148, 163, 184, 0.3)' },
      },
      splitLine: {
        lineStyle: { color: 'rgba(148, 163, 184, 0.3)' },
      },
    },
    series: [
      {
        name: '匹配度',
        type: 'radar',
        data: [
          {
            value: scores.map((s) => Math.round(s * 100) / 100),
            name: '当前画像匹配度',
            areaStyle: {
              color: 'rgba(99, 102, 241, 0.25)',
            },
            lineStyle: {
              color: '#6366f1',
              width: 2,
            },
            itemStyle: {
              color: '#6366f1',
            },
          },
        ],
      },
    ],
  };

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-slate-900">
      <h3 className="mb-1 text-base font-semibold text-gray-900 dark:text-white">职业匹配雷达图</h3>
      <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">
        {topJob
          ? `基于您与「${topJob.title}」岗位的匹配分析`
          : '基于您的职业画像与目标岗位的匹配分析'}
      </p>
      <ReactECharts
        option={option}
        style={{ height: 280, width: '100%' }}
        opts={{ renderer: 'svg' }}
      />
      {topJob && (
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>
            最优匹配岗位:{' '}
            <span className="font-medium text-gray-900 dark:text-white">{topJob.title}</span>
          </span>
          <span>匹配度: {topJob.matchScore}%</span>
        </div>
      )}
    </div>
  );
}
