import { useEffect, useState } from 'react'
import { useTheme } from './theme'

export const PASTEL = ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6', '#FFE7A3']

function read() {
  const cs = getComputedStyle(document.documentElement)
  const g = (name, fallback) => cs.getPropertyValue(name).trim() || fallback
  return {
    lavender: g('--lavender', PASTEL[0]),
    mint: g('--mint', PASTEL[1]),
    peach: g('--peach', PASTEL[2]),
    sky: g('--sky', PASTEL[3]),
    rose: g('--rose', PASTEL[4]),
    butter: g('--butter', PASTEL[5]),
    axis: g('--text-3', '#737A8A'),
    text: g('--text', '#1F2430'),
    grid: g('--border', '#ECE8E1'),
    surface: g('--surface', '#FFFFFF'),
    cursor: g('--surface-3', '#F1EEE8'),
  }
}

/** Chart colours resolved from the CSS tokens; updates when the theme toggles. */
export function useChartTheme() {
  const { theme } = useTheme()
  const [t, setT] = useState(read)
  useEffect(() => {
    const id = requestAnimationFrame(() => setT(read()))
    return () => cancelAnimationFrame(id)
  }, [theme])
  return t
}
