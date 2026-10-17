import { useMemo } from 'react'
import { useTheme } from './theme'

// Pastel series colours for charts (same hues as the CSS tokens).
export const PASTEL = ['#C7B9FF', '#A9D6FF', '#A7E8C8', '#FFC9A3', '#FFB8C6', '#FFE7A3']

const read = (name, fallback) => {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

/** Chart colours that follow the active theme (recomputed when the theme flips). */
export function useChartTheme() {
  const { theme } = useTheme()
  return useMemo(
    () => ({
      lavender: read('--lavender', '#C7B9FF'),
      mint: read('--mint', '#A7E8C8'),
      peach: read('--peach', '#FFC9A3'),
      sky: read('--sky', '#A9D6FF'),
      rose: read('--rose', '#FFB8C6'),
      butter: read('--butter', '#FFE7A3'),
      text: read('--text', '#1F2430'),
      axis: read('--text-3', '#737A8A'),
      grid: read('--border', '#ECE8E1'),
      surface: read('--surface', '#FFFFFF'),
      cursor: theme === 'dark' ? 'rgba(255,255,255,.06)' : 'rgba(31,36,48,.05)',
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [theme],
  )
}
