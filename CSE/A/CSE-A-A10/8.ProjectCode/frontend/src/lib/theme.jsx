import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useState } from 'react'

const KEY = 'fs_theme'
const ThemeContext = createContext(null)
export const useTheme = () => useContext(ThemeContext)

const TOKENS = ['bg', 'panel', 'panel-2', 'fg', 'muted', 'dim', 'line', 'line-strong', 'grid', 'ok', 'warn', 'hot', 'alert', 'info', 'cyan']

function readTokens() {
  const cs = getComputedStyle(document.documentElement)
  return Object.fromEntries(TOKENS.map((k) => [k.replace(/-(\w)/g, (_, c) => c.toUpperCase()), cs.getPropertyValue(`--${k}`).trim()]))
}
function saved() {
  try {
    const t = localStorage.getItem(KEY)
    return t === 'light' || t === 'dark' ? t : null
  } catch {
    return null
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => saved() || document.documentElement.dataset.theme || 'dark')
  const [explicit, setExplicit] = useState(() => !!saved())
  const [tokens, setTokens] = useState(readTokens)

  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme
    setTokens(readTokens())
  }, [theme])

  // Follow the OS preference until the user picks a theme explicitly.
  useEffect(() => {
    if (explicit) return
    const mq = window.matchMedia('(prefers-color-scheme: light)')
    const on = (e) => setTheme(e.matches ? 'light' : 'dark')
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [explicit])

  const toggle = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark'
    try { localStorage.setItem(KEY, next) } catch { /* private mode */ }
    setExplicit(true)
    setTheme(next)
  }, [theme])

  return <ThemeContext.Provider value={{ theme, tokens, toggle }}>{children}</ThemeContext.Provider>
}
