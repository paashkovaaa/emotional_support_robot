import { create } from 'zustand';

type Theme = 'light';

function applyTheme() {
  // Always light — remove dark class if it was previously set
  document.documentElement.classList.remove('dark');
  localStorage.removeItem('emi-theme');
}

interface ThemeState {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

export const useThemeStore = create<ThemeState>(() => {
  applyTheme();
  return {
    theme: 'light',
    isDark: false,
    toggleTheme: () => {},
    setTheme: () => {},
  };
});

