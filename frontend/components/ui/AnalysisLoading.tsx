'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { FileText, Search, Compass, Activity, LayoutTemplate } from 'lucide-react';

const STEPS = [
  {
    key: 'parse',
    icon: <FileText size={18} key="parse" />,
    name: '解析职业画像',
    desc: '提取技能、经验与目标...',
  },
  {
    key: 'retrieve',
    icon: <Search size={18} key="retrieve" />,
    name: '匹配岗位与策略',
    desc: '检索推荐岗位与发展路径...',
  },
  {
    key: 'architect',
    icon: <Compass size={18} key="architect" />,
    name: '生成职业策略',
    desc: '构建职业规划与行动计划...',
  },
  {
    key: 'simulate',
    icon: <Activity size={18} key="simulate" />,
    name: '模拟路径验证',
    desc: '推演不同策略的成功率...',
  },
  {
    key: 'render',
    icon: <LayoutTemplate size={18} key="render" />,
    name: '准备可视化结果',
    desc: '整理图表与建议...',
  },
] as const;

interface Props {
  /** 0-STEPS.length, which step is currently active */
  activeStep?: number;
}

export function AnalysisLoading({ activeStep = -1 }: Props) {
  const { t } = useI18n();
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [logMessages, setLogMessages] = useState<string[]>([]);

  // Auto-advance demo progress
  useEffect(() => {
    if (activeStep >= 0) {
      setCurrentStep(activeStep);
      setProgress((activeStep / STEPS.length) * 100);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        const next = prev + 1;
        if (next > STEPS.length) {
          clearInterval(interval);
          return prev;
        }
        setProgress((next / STEPS.length) * 100);
        return next;
      });
    }, 900);

    return () => clearInterval(interval);
  }, [activeStep]);

  // Generate log messages
  useEffect(() => {
    if (currentStep <= 0) return;
    const logs: string[] = [
      '> 正在初始化职业分析引擎...',
      `> 已提取 8 项技能，识别 3 个职业目标`,
      `> 匹配到 2 个推荐岗位，4 条发展策略`,
      `> 生成 5 步职业规划（预计 215 天）`,
      `> 完成 10 轮模拟，平均成功率 78%`,
      '> 分析完成，正在渲染结果...',
    ];
    if (currentStep <= logs.length) {
      setLogMessages((prev) => {
        const msg = logs[currentStep - 1];
        if (prev.includes(msg)) return prev;
        return [...prev.slice(-4), msg];
      });
    }
  }, [currentStep]);

  return (
    <div className="mx-auto w-full max-w-3xl">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="mb-2 flex items-center justify-between text-xs">
          <span className="font-mono text-slate-400">{t('pipeline.title')}</span>
          <span className="font-mono text-neon-cyan">{Math.round(progress)}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-neon-cyan via-neon-blue to-neon-purple"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-6 top-8 bottom-8 w-px bg-slate-800" />
        <motion.div
          className="absolute left-6 top-8 w-px bg-gradient-to-b from-neon-cyan via-neon-blue to-neon-purple"
          initial={{ height: 0 }}
          animate={{
            height:
              currentStep > 0
                ? `${((Math.min(currentStep, STEPS.length) - 0.5) / STEPS.length) * 100}%`
                : 0,
          }}
          transition={{ duration: 0.6 }}
        />

        <div className="space-y-3">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentStep;
            const isActive = idx === currentStep - 1 && currentStep <= STEPS.length;
            const isPending = idx >= currentStep;

            return (
              <motion.div
                key={step.key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.08 }}
                className="relative flex items-center gap-4"
              >
                {/* Status dot */}
                <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center">
                  <motion.div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl border transition-all duration-500 ${
                      isDone
                        ? 'border-neon-cyan/40 bg-cyan-500/10 text-neon-cyan'
                        : isActive
                          ? 'border-current bg-slate-800/80 text-neon-cyan shadow-lg shadow-cyan-500/30'
                          : 'border-slate-700/50 bg-slate-900/40 text-slate-600'
                    }`}
                    animate={
                      isActive
                        ? {
                            scale: [1, 1.08, 1],
                            boxShadow: [
                              '0 0 0px rgba(6,182,212,0)',
                              '0 0 20px rgba(6,182,212,0.3)',
                              '0 0 0px rgba(6,182,212,0)',
                            ],
                          }
                        : {}
                    }
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    {isDone ? (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path
                          d="M3 8L6.5 11.5L13 4.5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    ) : (
                      step.icon
                    )}
                  </motion.div>

                  {/* Ripple for active */}
                  {isActive && (
                    <motion.div
                      className="absolute inset-0 rounded-xl border border-current opacity-30"
                      animate={{ scale: [1, 1.4], opacity: [0.5, 0] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                    />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-semibold transition-colors duration-300 ${
                        isDone || isActive ? 'text-slate-200' : 'text-slate-600'
                      }`}
                    >
                      {step.name}
                    </span>
                    {isActive && (
                      <motion.span
                        className="text-[10px] font-mono text-neon-cyan"
                        animate={{ opacity: [1, 0.4, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                      >
                        {t('pipeline.running')}
                      </motion.span>
                    )}
                    {isDone && (
                      <span className="text-[10px] font-mono text-neon-green">
                        {t('pipeline.done')}
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-xs transition-colors duration-300 ${
                      isActive ? 'text-slate-400' : isPending ? 'text-slate-700' : 'text-slate-500'
                    }`}
                  >
                    {step.desc}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Terminal log */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-6 rounded-lg border border-slate-800 bg-slate-950/80 p-3 font-mono text-[11px]"
      >
        <div className="mb-1.5 flex items-center gap-1.5 text-slate-600">
          <div className="h-2 w-2 rounded-full bg-red-500/60" />
          <div className="h-2 w-2 rounded-full bg-amber-500/60" />
          <div className="h-2 w-2 rounded-full bg-green-500/60" />
          <span className="ml-1 text-[10px]">{t('pipeline.logTitle')}</span>
        </div>
        <div className="space-y-1">
          {logMessages.map((msg, i) => (
            <motion.div
              key={`${i}-${msg}`}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-slate-400"
            >
              <span className="text-slate-600">{String(i).padStart(2, '0')}:</span>{' '}
              <span className={msg.includes('完成') ? 'text-neon-green' : ''}>{msg}</span>
            </motion.div>
          ))}
          <motion.div
            animate={{ opacity: [1, 0] }}
            transition={{ repeat: Infinity, duration: 0.8 }}
            className="text-neon-cyan"
          >
            _
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
