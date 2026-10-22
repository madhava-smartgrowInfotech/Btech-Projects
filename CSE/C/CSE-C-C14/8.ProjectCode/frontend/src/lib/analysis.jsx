import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { api } from './api'

const Ctx = createContext(null)

/**
 * Holds the current analysis so the result survives moving between screens.
 * status: idle | running | done | error
 */
export function AnalysisProvider({ children }) {
  const [state, setState] = useState({ status: 'idle', file: null, previewUrl: null, result: null, error: null, startedAt: null })
  const abort = useRef(null)

  const choose = useCallback((file) => {
    setState((s) => {
      if (s.previewUrl) URL.revokeObjectURL(s.previewUrl)
      return { status: 'idle', file, previewUrl: file ? URL.createObjectURL(file) : null, result: null, error: null, startedAt: null }
    })
  }, [])

  const run = useCallback(async (file) => {
    abort.current?.abort()
    const ac = new AbortController()
    abort.current = ac
    setState((s) => ({ ...s, status: 'running', error: null, result: null, startedAt: Date.now() }))
    try {
      const result = await api.analyze(file, ac.signal)
      setState((s) => ({ ...s, status: 'done', result }))
      return result
    } catch (error) {
      if (error.name === 'AbortError') return null
      setState((s) => ({ ...s, status: 'error', error }))
      throw error
    }
  }, [])

  const cancel = useCallback(() => {
    abort.current?.abort()
    setState((s) => ({ ...s, status: 'idle', startedAt: null }))
  }, [])

  const reset = useCallback(() => choose(null), [choose])

  const value = useMemo(() => ({ ...state, choose, run, cancel, reset }), [state, choose, run, cancel, reset])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useAnalysis = () => useContext(Ctx)
