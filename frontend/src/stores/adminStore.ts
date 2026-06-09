import { create } from 'zustand';
import type { AdminUser, SystemStats, SystemHealth } from '../types';
import * as adminApi from '../api/admin';
import type { GetUsersParams } from '../api/admin';

interface AdminState {
  /* ── Користувачі ── */
  users: AdminUser[];
  usersTotal: number;
  usersPage: number;
  usersPerPage: number;
  usersPages: number;
  usersLoading: boolean;
  usersError: string | null;
  usersSearch: string;
  usersFilters: { role?: 'user' | 'admin'; is_blocked?: boolean };
  usersSortBy: string;
  usersSortOrder: 'asc' | 'desc';

  /* ── Статистика ── */
  stats: SystemStats | null;
  statsLoading: boolean;

  /* ── Здоров'я ── */
  health: SystemHealth | null;
  healthLoading: boolean;

  /* ── Дії ── */
  fetchUsers: (params?: GetUsersParams) => Promise<void>;
  setUsersPage: (page: number) => void;
  setUsersSearch: (search: string) => void;
  setUsersFilters: (filters: { role?: 'user' | 'admin'; is_blocked?: boolean }) => void;
  setUsersSort: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  blockUser: (userId: string, isBlocked: boolean, reason?: string) => Promise<string>;

  fetchStats: () => Promise<void>;
  fetchHealth: () => Promise<void>;
}

export const useAdminStore = create<AdminState>((set, get) => ({
  /* ── Початковий стан ── */
  users: [],
  usersTotal: 0,
  usersPage: 1,
  usersPerPage: 20,
  usersPages: 1,
  usersLoading: false,
  usersError: null,
  usersSearch: '',
  usersFilters: {},
  usersSortBy: 'created_at',
  usersSortOrder: 'desc',

  stats: null,
  statsLoading: false,

  health: null,
  healthLoading: false,

  /* ── Користувачі ── */
  fetchUsers: async (params) => {
    set({ usersLoading: true, usersError: null });
    try {
      const {
        usersPage,
        usersPerPage,
        usersSearch,
        usersFilters,
        usersSortBy,
        usersSortOrder,
      } = get();

      const merged: GetUsersParams = {
        page: usersPage,
        per_page: usersPerPage,
        search: usersSearch || undefined,
        sort_by: usersSortBy,
        sort_order: usersSortOrder,
        ...usersFilters,
        ...params,
      };

      const res = await adminApi.getUsers(merged);
      set({
        users: res.users,
        usersTotal: res.total,
        usersPage: res.page,
        usersPerPage: res.per_page,
        usersPages: res.pages,
        usersLoading: false,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Помилка завантаження';
      set({ usersError: msg, usersLoading: false });
    }
  },

  setUsersPage: (page) => {
    set({ usersPage: page });
    get().fetchUsers({ page });
  },

  setUsersSearch: (search) => {
    set({ usersSearch: search, usersPage: 1 });
    get().fetchUsers({ search: search || undefined, page: 1 });
  },

  setUsersFilters: (filters) => {
    set({ usersFilters: filters, usersPage: 1 });
    get().fetchUsers({ ...filters, page: 1 });
  },

  setUsersSort: (sortBy, sortOrder) => {
    set({ usersSortBy: sortBy, usersSortOrder: sortOrder, usersPage: 1 });
    get().fetchUsers({ sort_by: sortBy, sort_order: sortOrder, page: 1 });
  },

  blockUser: async (userId, isBlocked, reason) => {
    const res = await adminApi.blockUser(userId, { is_blocked: isBlocked, reason });
    // Оновлюємо список
    await get().fetchUsers();
    return res.message;
  },

  /* ── Статистика ── */
  fetchStats: async () => {
    set({ statsLoading: true });
    try {
      const stats = await adminApi.getSystemStats();
      set({ stats, statsLoading: false });
    } catch {
      set({ statsLoading: false });
    }
  },

  /* ── Здоров'я ── */
  fetchHealth: async () => {
    set({ healthLoading: true });
    try {
      const health = await adminApi.getSystemHealth();
      set({ health, healthLoading: false });
    } catch {
      set({ healthLoading: false });
    }
  },
}));

