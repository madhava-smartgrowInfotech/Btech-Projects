import { useTheme } from './theme'

export const PASTEL = ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6', '#FFE7A3']

/** Chart colours that follow the active theme. */
export function useChartTheme() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  return {
    lavender: '#C7B9FF',
    mint: '#A7E8C8',
    peach: '#FFC9A3',
    sky: '#A9D6FF',
    rose: '#FFB8C6',
    butter: '#FFE7A3',
    axis: dark ? '#A19B95' : '#737A8A',
    text: dark ? '#F3F0EB' : '#1F2430',
    grid: dark ? '#403E47' : '#ECE8E1',
    cursor: dark ? 'rgba(199,185,255,.12)' : 'rgba(199,185,255,.22)',
    surface: dark ? '#2E2D35' : '#FFFFFF',
  }
}
