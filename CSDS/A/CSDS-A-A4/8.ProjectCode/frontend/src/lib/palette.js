import { useTheme } from './theme'

// Chart fills per theme (Recharts needs concrete colour values, not CSS variables).
export const PASTEL = ['#B9A8FF', '#86DDB4', '#FFB685', '#8CC8FF', '#FFA8BB', '#F0D070', '#8FDADA', '#D9B8F5', '#C4E58F', '#F7B4E6']

export function useChartTheme() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  return {
    dark,
    grid: dark ? '#403E47' : '#EEEAE3',
    axis: dark ? '#A19B95' : '#737A8A',
    text: dark ? '#F3F0EB' : '#1F2430',
    surface: dark ? '#2E2D35' : '#FFFFFF',
    lavender: '#B9A8FF',
    mint: '#86DDB4',
    peach: '#FFB685',
    sky: '#8CC8FF',
    rose: '#FFA8BB',
    muted: dark ? '#5A5863' : '#E2DCD3',
    cursor: dark ? 'rgba(199,185,255,.10)' : 'rgba(199,185,255,.20)',
  }
}
