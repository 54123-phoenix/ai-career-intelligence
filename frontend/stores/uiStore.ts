import { create } from 'zustand';

interface ToastItem {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface UIState {
  sidebarOpen: boolean;
  toast: ToastItem | null;
  setSidebarOpen: (open: boolean) => void;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  clearToast: () => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  toast: null,

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  showToast: (message, type = 'info') => {
    const id = Math.random().toString(36).slice(2);
    set({ toast: { id, message, type } });
    setTimeout(() => set({ toast: null }), 3000);
  },

  clearToast: () => set({ toast: null }),
}));
