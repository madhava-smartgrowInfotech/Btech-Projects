import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Persona } from '@/lib/types'

function uuid(): string {
  const c = globalThis.crypto
  if (c && typeof c.randomUUID === 'function') return c.randomUUID()
  // RFC4122-ish fallback for non-secure contexts
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (ch) => {
    const r = (Math.random() * 16) | 0
    const v = ch === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

type SessionState = {
  sessionId: string
  userId?: string
  persona?: Persona
  setPersona: (persona: Persona | undefined) => void
  resetSession: () => void
}

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      sessionId: uuid(),
      userId: undefined,
      persona: undefined,
      setPersona: (persona) => set({ persona, userId: persona?.id }),
      resetSession: () => set({ sessionId: uuid() }),
    }),
    {
      name: 'nuvara.session',
      version: 1,
    },
  ),
)
