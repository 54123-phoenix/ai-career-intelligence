'use client';

import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { useI18n } from '@/lib/i18n';
import { Sparkles, User, Briefcase, MapPin, GraduationCap } from 'lucide-react';
import type { UserProfile } from '@/types/t008';

interface Props {
  userInput: string;
  setUserInput: (v: string) => void;
  onRun: () => void;
  loading: boolean;
  profile: UserProfile | null;
}

export function ActOneInput({ userInput, setUserInput, onRun, loading, profile }: Props) {
  const { t } = useI18n();

  return (
    <section className="space-y-4">
      <SectionHeader
        title={t('actOne.title')}
        subtitle={t('actOne.subtitle')}
        icon={<Sparkles size={18} />}
      />

      <GlassCard glow="cyan" delay={0.1}>
        <div className="flex flex-col gap-3 md:flex-row md:items-end">
          <div className="flex-1">
            <label className="mb-1 block text-xs font-medium text-slate-400">
              {t('actOne.inputLabel')}
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-slate-700/50 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-neon-cyan focus:outline-none focus:ring-1 focus:ring-neon-cyan/30"
              placeholder={t('actOne.inputPlaceholder')}
            />
          </div>
          <button
            onClick={onRun}
            disabled={loading}
            className="shrink-0 rounded-lg bg-gradient-to-r from-neon-cyan to-neon-blue px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:shadow-cyan-500/40 disabled:opacity-50 disabled:hover:shadow-none"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                {t('actOne.runningBtn')}
              </span>
            ) : (
              t('actOne.runBtn')
            )}
          </button>
        </div>
      </GlassCard>

      {profile && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          <GlassCard glow="blue" delay={0.25} className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/10 text-neon-blue">
              <User size={20} />
            </div>
            <div>
              <div className="text-xs text-slate-400">{t('actOne.experience')}</div>
              <div className="text-lg font-bold text-slate-100">
                <AnimatedNumber value={profile.experience_years} suffix={t('actOne.yearSuffix')} />
              </div>
            </div>
          </GlassCard>

          <GlassCard glow="purple" delay={0.3} className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-500/10 text-neon-purple">
              <GraduationCap size={20} />
            </div>
            <div>
              <div className="text-xs text-slate-400">{t('actOne.education')}</div>
              <div className="text-lg font-bold text-slate-100">
                {profile.education_level || '—'}
              </div>
            </div>
          </GlassCard>

          <GlassCard glow="green" delay={0.35} className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-neon-green">
              <Briefcase size={20} />
            </div>
            <div>
              <div className="text-xs text-slate-400">{t('actOne.skillsParsed')}</div>
              <div className="text-lg font-bold text-slate-100">
                <AnimatedNumber value={profile.skills.length} />
              </div>
            </div>
          </GlassCard>

          <GlassCard glow="orange" delay={0.4} className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/10 text-neon-orange">
              <MapPin size={20} />
            </div>
            <div>
              <div className="text-xs text-slate-400">{t('actOne.locations')}</div>
              <div className="text-lg font-bold text-slate-100">
                {profile.preferred_locations.slice(0, 2).join(', ') || '—'}
              </div>
            </div>
          </GlassCard>

          <GlassCard delay={0.45} className="md:col-span-2 lg:col-span-4">
            <div className="mb-2 text-xs font-medium text-slate-400">{t('actOne.parsedSkills')}</div>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill, i) => (
                <motion.span
                  key={skill}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.03 }}
                  className="rounded-md bg-cyan-500/10 px-2.5 py-1 text-xs font-medium text-neon-cyan ring-1 ring-cyan-500/20"
                >
                  {skill}
                </motion.span>
              ))}
            </div>
          </GlassCard>

          <GlassCard delay={0.5} className="md:col-span-2 lg:col-span-4">
            <div className="mb-2 text-xs font-medium text-slate-400">{t('actOne.careerGoals')}</div>
            <div className="flex flex-wrap gap-2">
              {profile.career_goals.map((goal, i) => (
                <motion.span
                  key={goal}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.55 + i * 0.05 }}
                  className="rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-neon-green ring-1 ring-emerald-500/20"
                >
                  {goal}
                </motion.span>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      )}
    </section>
  );
}
