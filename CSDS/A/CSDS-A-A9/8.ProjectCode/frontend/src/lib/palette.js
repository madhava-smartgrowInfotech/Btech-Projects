import { useEffect, useState } from 'react'
import { useTheme } from './theme'

export const PASTEL = ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6', '#FFE7A3']

const LIGHT = { axis: '#737A8A', grid: '#ECE8E1', text: '#1F2430', surface: '#FFFFFF', cursor: 'rgba(199,185,255,.18)' }
const DARK = { axis: '#A19B95', grid: '#403E47', text: '#F3F0EB', surface: '#2E2D35', cursor: 'rgba(199,185,255,.14)' }

/** Chart colours that follow the active theme. */
export function useChartTheme() {
  const { theme } = useTheme()
  const [, bump] = useState(0)
  useEffect(() => bump((n) => n + 1), [theme])
  const base = theme === 'dark' ? DARK : LIGHT
  return { ...base, lavender: PASTEL[0], mint: PASTEL[1], peach: PASTEL[2], sky: PASTEL[3], rose: PASTEL[4], butter: PASTEL[5] }
}
