import { useTheme } from './theme'

// Pastel series colours (same hues as the CSS tokens).
export const PASTEL = ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6', '#FFE7A3']

const LIGHT = {
  lavender: '#9D8BF5',
  mint: '#6FD1A2',
  peach: '#FFB27A',
  sky: '#7DBBFA',
  rose: '#FF94AA',
  axis: '#737A8A',
  grid: '#ECE8E1',
  text: '#4E5566',
  surface: '#FFFFFF',
  cursor: 'rgba(199, 185, 255, 0.18)',
}
const DARK = {
  lavender: '#C7B9FF',
  mint: '#A7E8C8',
  peach: '#FFC9A3',
  sky: '#A9D6FF',
  rose: '#FFB8C6',
  axis: '#A19B95',
  grid: '#403E47',
  text: '#CBC5BE',
  surface: '#2E2D35',
  cursor: 'rgba(199, 185, 255, 0.14)',
}

/** Chart colours that follow the light/dark theme. */
export function useChartTheme() {
  const { theme } = useTheme()
  return theme === 'dark' ? DARK : LIGHT
}
