import { create } from 'zustand';
import type { CareerAnalysisResult } from '@/types/career';
import { analyzeCareer } from '@/lib/api/career';

interface CareerState {
  currentAnalysis: CareerAnalysisResult | null;
  history: CareerAnalysisResult[];
  isAnalyzing: boolean;
  error: string | null;
  runAnalysis: (input: string) => Promise<void>;
  clearAnalysis: () => void;
  addToHistory: (result: CareerAnalysisResult) => void;
}

export const useCareerStore = create<CareerState>()((set, get) => ({
  currentAnalysis: null,
  history: [],
  isAnalyzing: false,
  error: null,

  runAnalysis: async (input: string) => {
    set({ isAnalyzing: true, error: null });
    try {
      const result = await analyzeCareer({ user_input: input, depth: 'standard' });
      set({ currentAnalysis: result.data, isAnalyzing: false });
      get().addToHistory(result.data);
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : '分析失败',
        isAnalyzing: false,
      });
    }
  },

  clearAnalysis: () => set({ currentAnalysis: null, error: null }),

  addToHistory: (result: CareerAnalysisResult) => {
    set((state) => ({
      history: [result, ...state.history].slice(0, 50),
    }));
  },
}));
