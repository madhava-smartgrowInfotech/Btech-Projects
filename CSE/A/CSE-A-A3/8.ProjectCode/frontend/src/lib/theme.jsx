import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const ThemeCtx = createContext({ theme: 'dark', toggle: () => {} })
const KEY = 'mdp-theme'

function saved() {
  try {
    const t = localStorage.getItem(KEY)
    return t === 'light' || t === 'dark' ? t : null
  } catch {
    return null
  }
}

const system = () => (window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark')

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => saved() || system())
  // apply the attribute before re-rendering so components that read computed tokens see the new theme
  const setTheme = useCallback((next) => {
    setThemeState((t) => {
      const value = typeof next === 'function' ? next(t) : next
      document.documentElement.setAttribute('data-theme', value)
      return value
    })
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', theme === 'dark' ? '#07090C' : '#F3F6F5')
  }, [theme])

  // follow the OS setting until the user picks a theme explicitly
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: light)')
    const on = () => {
      if (!saved()) setTheme(mq.matches ? 'light' : 'dark')
    }
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [setTheme])

  const toggle = useCallback(() => {
    setTheme((t) => {
      const next = t === 'dark' ? 'light' : 'dark'
      try {
        localStorage.setItem(KEY, next)
      } catch {
        /* storage unavailable - theme still switches for this visit */
      }
      return next
    })
  }, [setTheme])

  return <ThemeCtx.Provider value={{ theme, toggle }}>{children}</ThemeCtx.Provider>
}

export const useTheme = () => useContext(ThemeCtx)
