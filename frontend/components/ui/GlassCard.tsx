'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface GlassCardProps {
  children?: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'none';
  animate?: boolean;
  delay?: number;
  onClick?: () => void;
}

const glowMap = {
  cyan: 'glow-cyan border-cyan-500/20',
  blue: 'glow-blue border-blue-500/20',
  green: 'glow-green border-emerald-500/20',
  orange: 'glow-orange border-amber-500/20',
  red: 'glow-red border-red-500/20',
  purple: 'border-violet-500/20',
  none: 'border-slate-700/30',
};

export function GlassCard({
  children,
  className,
  glow = 'none',
  animate = true,
  delay = 0,
  onClick,
}: GlassCardProps) {
  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 20 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
      className={cn(
        'glass-card p-5',
        glowMap[glow],
        onClick && 'cursor-pointer transition-transform hover:scale-[1.01] active:scale-[0.99]',
        className
      )}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}
