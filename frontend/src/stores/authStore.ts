import { create } from 'zustand';
import type { User, Profile } from '../types';
import * as authApi from '../api/auth';

interface AuthState {
  /** Поточний користувач */
  user: User | null;
  /** Профіль користувача */
  profile: Profile | null;
  /** Чи авторизований */
  isAuthenticated: boolean;
  /** Чи завантажується стан */
  loading: boolean;
  /** Чи ініціалізовано (перша перевірка токена) */
  initialized: boolean;

  // ── Дії ──
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, nickname: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  loadProfile: () => Promise<void>;
  completeSurvey: (data: Parameters<typeof authApi.completeSurvey>[0]) => Promise<Profile>;
  updateProfile: (data: Parameters<typeof authApi.updateProfile>[0]) => Promise<Profile>;
  deleteAccount: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  profile: null,
  isAuthenticated: false,
  loading: false,
  initialized: false,

  login: async (email, password) => {
    const tokens = await authApi.login({ email, password });
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    set({ isAuthenticated: true });
    await get().loadUser();
    await get().loadProfile();
  },

  register: async (email, password, nickname) => {
    await authApi.register({ email, password, nickname });
    // Після реєстрації — автоматичний логін
    await get().login(email, password);
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // Ігноруємо помилки при логауті
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, profile: null, isAuthenticated: false });
  },

  loadUser: async () => {
    set({ loading: true });
    try {
      const user = await authApi.getCurrentUser();
      set({ user, isAuthenticated: true, loading: false });
    } catch {
      set({ user: null, isAuthenticated: false, loading: false });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      set({ initialized: true });
    }
  },

  loadProfile: async () => {
    try {
      const profile = await authApi.getProfile();
      set({ profile });
    } catch {
      set({ profile: null });
    }
  },

  completeSurvey: async (data) => {
    const profile = await authApi.completeSurvey(data);
    set({ profile });
    return profile;
  },

  updateProfile: async (data) => {
    const profile = await authApi.updateProfile(data);
    set({ profile });
    return profile;
  },

  deleteAccount: async () => {
    await authApi.deleteAccount();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, profile: null, isAuthenticated: false });
  },
}));

