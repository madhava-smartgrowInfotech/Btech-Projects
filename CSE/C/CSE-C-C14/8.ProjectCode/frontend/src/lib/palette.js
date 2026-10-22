import { useMemo } from 'react'
import { useTheme } from './theme'

// Pastel series colours used by the chart wrappers (same hues as the CSS tokens).
export const PASTEL = ['#C7B9FF', '#A9D6FF', '#A7E8C8', '#FFC9A3', '#FFB8C6', '#FFE7A3']

export function useChartTheme() {
  const { theme } = useTheme()
  return useMemo(() => {
    const dark = theme === 'dark'
    return {
      lavender: '#C7B9FF',
      sky: '#A9D6FF',
      mint: '#A7E8C8',
      peach: '#FFC9A3',
      rose: '#FFB8C6',
      butter: '#FFE7A3',
      axis: dark ? '#A19B95' : '#737A8A',
      text: dark ? '#F3F0EB' : '#1F2430',
      grid: dark ? '#403E47' : '#ECE8E1',
      surface: dark ? '#2E2D35' : '#FFFFFF',
      cursor: dark ? 'rgba(199,185,255,.12)' : 'rgba(199,185,255,.22)',
    }
  }, [theme])
}
