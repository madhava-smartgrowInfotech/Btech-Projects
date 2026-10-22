import { useMemo } from 'react'
import { useTheme } from '../../lib/theme'

// Resolve design tokens to concrete colours (SVG attributes and WebGL cannot use CSS variables).
export function useChartColors() {
  const { theme } = useTheme()
  return useMemo(() => {
    const cs = getComputedStyle(document.documentElement)
    const v = (n) => cs.getPropertyValue(n).trim()
    return {
      theme,
      accent: v('--accent'),
      accent2: v('--accent-2'),
      danger: v('--danger'),
      warn: v('--warn'),
      info: v('--info'),
      text: v('--text'),
      text2: v('--text-2'),
      text3: v('--text-3'),
      grid: v('--chart-grid'),
      panel: v('--panel'),
      violet: v('--violet'),
      series: [v('--accent'), v('--info'), v('--violet'), v('--warn')],
      label: { accept: v('--accent'), borderline: v('--warn'), reject: v('--danger') },
    }
  }, [theme])
}
