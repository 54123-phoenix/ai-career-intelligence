'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, subtitle, icon, className }: SectionHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className={cn('mb-4 flex items-center gap-3', className)}
    >
      {icon && (
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-neon-cyan">
          {icon}
        </div>
      )}
      <div>
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
    </motion.div>
  );
}
