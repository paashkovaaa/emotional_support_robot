import { create } from 'zustand';
import type { EmotionEntry, EmotionGenerateResponse } from '../types';
import * as emotionsApi from '../api/emotions';

interface EmotionState {
  /** Записи за поточний місяць */
  entries: EmotionEntry[];
  /** Поточний обраний запис (для перегляду/редагування) */
  selectedEntry: EmotionEntry | null;
  /** Поточний місяць і рік */
  currentMonth: number;
  currentYear: number;
  /** Стан завантаження */
  loading: boolean;
  /** Помилка */
  error: string | null;
  /** Пропозиція бота (для модалки) */
  botSuggestion: EmotionGenerateResponse | null;
  botSuggestionLoading: boolean;

  // ── Дії ──
  setMonthYear: (month: number, year: number) => void;
  fetchEntries: (month: number, year: number) => Promise<void>;
  selectEntry: (entry: EmotionEntry | null) => void;
  createEntry: (data: Parameters<typeof emotionsApi.createEmotionEntry>[0]) => Promise<EmotionEntry>;
  updateEntry: (
    id: string,
    data: Parameters<typeof emotionsApi.updateEmotionEntry>[1],
  ) => Promise<EmotionEntry>;
  deleteEntry: (id: string) => Promise<void>;
  generateSuggestion: (conversationId: string, entryDate?: string) => Promise<void>;
  clearSuggestion: () => void;
}

const now = new Date();

export const useEmotionStore = create<EmotionState>((set, get) => ({
  entries: [],
  selectedEntry: null,
  currentMonth: now.getMonth() + 1,
  currentYear: now.getFullYear(),
  loading: false,
  error: null,
  botSuggestion: null,
  botSuggestionLoading: false,

  setMonthYear: (month, year) => {
    set({ currentMonth: month, currentYear: year });
    get().fetchEntries(month, year);
  },

  fetchEntries: async (month, year) => {
    set({ loading: true, error: null });
    try {
      const entries = await emotionsApi.getEntriesByMonth(month, year);
      set({ entries, loading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Не вдалося завантажити записи';
      set({ error: message, loading: false });
    }
  },

  selectEntry: (entry) => set({ selectedEntry: entry }),

  createEntry: async (data) => {
    const entry = await emotionsApi.createEmotionEntry(data);
    const { currentMonth, currentYear } = get();
    // Перезавантажуємо записи за поточний місяць
    await get().fetchEntries(currentMonth, currentYear);
    return entry;
  },

  updateEntry: async (id, data) => {
    const updated = await emotionsApi.updateEmotionEntry(id, data);
    const { currentMonth, currentYear } = get();
    await get().fetchEntries(currentMonth, currentYear);
    set({ selectedEntry: updated });
    return updated;
  },

  deleteEntry: async (id) => {
    await emotionsApi.deleteEmotionEntry(id);
    const { currentMonth, currentYear } = get();
    await get().fetchEntries(currentMonth, currentYear);
    set({ selectedEntry: null });
  },

  generateSuggestion: async (conversationId, entryDate) => {
    set({ botSuggestionLoading: true });
    try {
      const suggestion = await emotionsApi.generateEmotionSummary({
        conversation_id: conversationId,
        entry_date: entryDate ?? null,
      });
      set({ botSuggestion: suggestion, botSuggestionLoading: false });
    } catch {
      set({ botSuggestionLoading: false });
    }
  },

  clearSuggestion: () => set({ botSuggestion: null }),
}));

