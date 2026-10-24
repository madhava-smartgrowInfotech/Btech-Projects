import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const ThemeCtx = createContext({ theme: 'light', toggle: () => {} })
const KEY = 'botgraph-theme'

function initial() {
  const t = document.documentElement.dataset.theme
  if (t === 'light' || t === 'dark') return t
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(initial)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])
  // follow the OS until the user picks a theme explicitly
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const on = (e) => {
      let saved = null
      try {
        saved = localStorage.getItem(KEY)
      } catch {
        /* storage blocked */
      }
      if (!saved) setTheme(e.matches ? 'dark' : 'light')
    }
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  const toggle = useCallback(() => {
    setTheme((t) => {
      const n = t === 'dark' ? 'light' : 'dark'
      try {
        localStorage.setItem(KEY, n)
      } catch {
        /* storage blocked */
      }
      return n
    })
  }, [])
  return <ThemeCtx.Provider value={{ theme, toggle }}>{children}</ThemeCtx.Provider>
}

export const useTheme = () => useContext(ThemeCtx)
