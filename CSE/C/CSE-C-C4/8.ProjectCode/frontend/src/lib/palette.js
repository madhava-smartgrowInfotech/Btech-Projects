import { useMemo } from 'react'
import { useTheme } from './theme'

// Pastel fills (cards, badges, bars) - kept identical to the CSS tokens.
export const PASTEL = ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6', '#FFE7A3']

// Line / stroke colours: a touch deeper in light mode so thin lines stay readable on white.
const LIGHT = {
  lavender: '#8B76F0',
  mint: '#3FBF86',
  peach: '#F29B62',
  sky: '#5AA7E8',
  rose: '#EE7690',
  butter: '#E5BF52',
  axis: '#737A8A',
  grid: '#ECE8E1',
  text: '#1F2430',
  surface: '#FFFFFF',
  cursor: 'rgba(199, 185, 255, .22)',
}
const DARK = {
  lavender: '#C7B9FF',
  mint: '#A7E8C8',
  peach: '#FFC9A3',
  sky: '#A9D6FF',
  rose: '#FFB8C6',
  butter: '#FFE7A3',
  axis: '#A19B95',
  grid: '#403E47',
  text: '#F3F0EB',
  surface: '#2E2D35',
  cursor: 'rgba(199, 185, 255, .14)',
}

export function useChartTheme() {
  const { theme } = useTheme()
  return useMemo(() => (theme === 'dark' ? DARK : LIGHT), [theme])
}
