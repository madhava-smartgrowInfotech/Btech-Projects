import { useCallback, useState } from 'react'
import { useToast } from '../components/ui'
import { useLab } from '../lib/lab'

/** Runs an API call, refreshes shared state, and reports success/failure via toast. */
export function useAction() {
  const toast = useToast()
  const { refresh } = useLab()
  const [busy, setBusy] = useState(null)
  const run = useCallback(
    async (name, fn, success) => {
      setBusy(name)
      try {
        const out = await fn()
        await refresh().catch(() => {})
        if (success) {
          toast({ kind: 'success', title: success.title, message: typeof success.message === 'function' ? success.message(out) : success.message })
        }
        return out
      } catch (e) {
        toast({ kind: 'error', title: success?.failTitle || 'Request failed', message: e.message, duration: 8000 })
        return null
      } finally {
        setBusy(null)
      }
    },
    [refresh, toast],
  )
  return { busy, run }
}
