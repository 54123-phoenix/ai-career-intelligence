'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import {
  FileText,
  Search,
  ShieldCheck,
  Compass,
  Activity,
  LayoutTemplate,
} from 'lucide-react';

const AGENT_ICONS = [
  <FileText size={18} key="parser" />,
  <Search size={18} key="retrieval" />,
  <ShieldCheck size={18} key="reviewer" />,
  <Compass size={18} key="architect" />,
  <Activity size={18} key="simulator" />,
  <LayoutTemplate size={18} key="frontend" />,
];

const AGENT_KEYS = ['parser', 'retrieval', 'reviewer', 'architect', 'simulator', 'frontend'] as const;

interface Props {
  /** 0-6, which step is currently active */
  activeStep?: number;
}

export function PipelineLoading({ activeStep = -1 }: Props) {
  const { t } = useI18n();
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [logMessages, setLogMessages] = useState<string[]>([]);

  // Auto-advance demo progress
  useEffect(() => {
    if (activeStep >= 0) {
      setCurrentStep(activeStep);
      setProgress((activeStep / AGENT_KEYS.length) * 100);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        const next = prev + 1;
        if (next > AGENT_KEYS.length) {
          clearInterval(interval);
          return prev;
        }
        setProgress((next / AGENT_KEYS.length) * 100);
        return next;
      });
    }, 900);

    return () => clearInterval(interval);
  }, [activeStep]);

  // Generate log messages
  useEffect(() => {
    if (currentStep <= 0) return;
    const logs: string[] = [
      '> Initializing multi-agent pipeline...',
      `> ParserAgent: Extracted 8 skills, 3 career goals`,
      `> RetrievalAgent: Matched 2 jobs, 4 strategy candidates`,
      `> ReviewerAgent: Applied RL weights, top score 0.87`,
      `> ArchitectAgent: Generated 5-step career plan (215 days)`,
      `> SimulatorAgent: Completed 10 rounds, success rate 78%`,
      `> FrontendAgent: Preparing visualization data...`,
      '> Pipeline complete. Rendering dashboard.',
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
          <span className="font-mono text-neon-cyan">
            {Math.round(progress)}%
          </span>
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

      {/* Agent steps */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-6 top-8 bottom-8 w-px bg-slate-800" />
        <motion.div
          className="absolute left-6 top-8 w-px bg-gradient-to-b from-neon-cyan via-neon-blue to-neon-purple"
          initial={{ height: 0 }}
          animate={{
            height: currentStep > 0
              ? `${((Math.min(currentStep, AGENT_KEYS.length) - 0.5) / AGENT_KEYS.length) * 100}%`
              : 0,
          }}
          transition={{ duration: 0.6 }}
        />

        <div className="space-y-3">
          {AGENT_KEYS.map((key, idx) => {
            const isDone = idx < currentStep;
            const isActive = idx === currentStep - 1 && currentStep <= AGENT_KEYS.length;
            const isPending = idx >= currentStep;
            const name = t(`pipeline.agents.${key}.name`);
            const desc = t(`pipeline.agents.${key}.desc`);

            return (
              <motion.div
                key={key}
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
                      AGENT_ICONS[idx]
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
                      {name}
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
                      <span className="text-[10px] font-mono text-neon-green">{t('pipeline.done')}</span>
                    )}
                  </div>
                  <p
                    className={`text-xs transition-colors duration-300 ${
                      isActive ? 'text-slate-400' : isPending ? 'text-slate-700' : 'text-slate-500'
                    }`}
                  >
                    {desc}
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
              <span className={msg.includes('complete') ? 'text-neon-green' : ''}>{msg}</span>
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
