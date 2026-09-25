import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AgentWeights, FeedbackAction } from '@/lib/types'

export type ActivityEntry = {
  id: string
  at: string
  action: FeedbackAction
  recId: string
  label: string
  surface: string
  learningStep?: number
  weights?: AgentWeights
  acknowledged: boolean
}

type ActivityState = {
  entries: ActivityEntry[]
  push: (entry: Omit<ActivityEntry, 'id' | 'at'>) => void
  clear: () => void
}

/**
 * Local mirror of the feedback signals this browser has emitted. The service is the
 * source of truth; this keeps the learning panel populated the instant a signal fires,
 * before the next weights poll lands.
 */
export const useActivity = create<ActivityState>()(
  persist(
    (set) => ({
      entries: [],
      push: (entry) =>
        set((state) => ({
          entries: [
            { ...entry, id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, at: new Date().toISOString() },
            ...state.entries,
          ].slice(0, 40),
        })),
      clear: () => set({ entries: [] }),
    }),
    { name: 'nuvara.activity', version: 1 },
  ),
)
