'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Lightbulb, ShieldAlert, BookOpen } from 'lucide-react';
import { useI18n } from '@/lib/i18n';
import type { T010PipelineOutput } from '@/types/t010';

interface Props {
  nodeName: string | null;
  data: T010PipelineOutput | null;
  onClose: () => void;
}

export function NodeDetailDrawer({ nodeName, data, onClose }: Props) {
  const { t } = useI18n();
  const nodeInfo = nodeName && data?.interactive_nodes?.[nodeName];

  return (
    <AnimatePresence>
      {nodeName && nodeInfo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 backdrop-blur-sm sm:items-center"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="glass-card m-4 w-full max-w-lg border-cyan-500/20 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-neon-cyan">
                  <BookOpen size={16} />
                </div>
                <h3 className="text-lg font-semibold text-slate-100">{nodeName}</h3>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-slate-200"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              {!!nodeInfo.description && (
                <div>
                  <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-slate-400">
                    <BookOpen size={12} />
                    {t('drawer.description')}
                  </div>
                  <p className="text-sm leading-relaxed text-slate-300">{nodeInfo.description as string}</p>
                </div>
              )}

              {!!nodeInfo.strategy_note && (
                <div className="rounded-lg bg-cyan-500/5 p-3 ring-1 ring-cyan-500/10">
                  <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-neon-cyan">
                    <Lightbulb size={12} />
                    {t('drawer.strategyNote')}
                  </div>
                  <p className="text-sm leading-relaxed text-slate-300">{nodeInfo.strategy_note as string}</p>
                </div>
              )}

              {!!nodeInfo.risk_note && (
                <div className="rounded-lg bg-orange-500/5 p-3 ring-1 ring-orange-500/10">
                  <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-neon-orange">
                    <ShieldAlert size={12} />
                    {t('drawer.riskWarning')}
                  </div>
                  <p className="text-sm leading-relaxed text-slate-300">{nodeInfo.risk_note as string}</p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
