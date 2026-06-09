/**
 * Хук для теми — завжди light.
 */
export function useTheme() {
  return {
    theme: 'light' as const,
    isDark: false,
    toggleTheme: () => {},
    setLight: () => {},
    setDark: () => {},
  };
}

