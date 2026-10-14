// Chart colours for the kit's Recharts wrappers. The values mirror the tokens in styles/index.css,
// so charts re-theme in the same render as the page (CSS variables are only readable after commit).
import { useTheme } from './theme.jsx'

// Ink tones: readable as lines and bars on both the light and the dark surface.
const LIGHT = {
  text: '#1F2430',
  axis: '#737A8A',
  grid: '#ECE8E1',
  surface: '#FFFFFF',
  cursor: '#F1EEE8',
  lavender: '#5B45C9',
  mint: '#1C7A50',
  peach: '#A9541A',
  sky: '#1F6AAE',
  rose: '#B13A55',
  butter: '#8A6D00',
}

const DARK = {
  text: '#F3F0EB',
  axis: '#A19B95',
  grid: '#403E47',
  surface: '#2E2D35',
  cursor: '#3B3A43',
  lavender: '#D2C7FF',
  mint: '#A7E8C8',
  peach: '#FFC9A3',
  sky: '#B9DDFF',
  rose: '#FFC2CE',
  butter: '#FFE7A3',
}

// Default series colours used by the kit when a series sets no colour.
export const PASTEL = [LIGHT.lavender, LIGHT.mint, LIGHT.peach, LIGHT.sky, LIGHT.rose]

export function useChartTheme() {
  const { theme } = useTheme()
  return theme === 'dark' ? DARK : LIGHT
}
