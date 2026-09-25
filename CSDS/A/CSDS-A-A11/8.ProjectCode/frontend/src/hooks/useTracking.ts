import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, queryKeys } from '@/lib/api'
import type { EventType, FeedbackAction, Product } from '@/lib/types'
import { useSession } from '@/store/session'
import { useActivity } from '@/store/activity'

type TrackArgs = {
  type: EventType
  product?: Product | null
  productId?: string | number
  query?: string
  value?: number
  recId?: string
  sourceAgent?: string
}

type SignalArgs = {
  action: FeedbackAction
  recId?: string
  product?: Product | null
  surface: string
  value?: number
}

/**
 * Single entry point for behavioural telemetry. Every meaningful interaction goes
 * through here: the event stream always gets it, and anything that originated from a
 * recommendation impression additionally closes the learning loop via /feedback.
 */
export function useTracking() {
  const sessionId = useSession((s) => s.sessionId)
  const userId = useSession((s) => s.userId)
  const pushActivity = useActivity((s) => s.push)
  const qc = useQueryClient()

  const track = useCallback(
    (args: TrackArgs) => {
      const productId = args.productId ?? args.product?.id
      void api.trackEvent({
        session_id: sessionId,
        user_id: userId,
        product_id: productId,
        type: args.type,
        query: args.query,
        value: args.value,
        rec_id: args.recId,
        source_agent: args.sourceAgent,
      })
    },
    [sessionId, userId],
  )

  /** Records the event AND, when tied to a recommendation, the reinforcement signal. */
  const signal = useCallback(
    async (args: SignalArgs) => {
      const eventType: EventType =
        args.action === 'add_to_cart'
          ? 'add_to_cart'
          : args.action === 'purchase'
            ? 'purchase'
            : 'click'

      track({
        type: eventType,
        product: args.product,
        recId: args.recId,
        value: args.value ?? args.product?.price,
      })

      if (!args.recId) return

      const label = args.product?.name ?? 'Recommended item'
      const res = await api.feedback({
        session_id: sessionId,
        user_id: userId,
        rec_id: args.recId,
        action: args.action,
      })

      pushActivity({
        action: args.action,
        recId: args.recId,
        label,
        surface: args.surface,
        learningStep: res?.learning_step,
        weights: res?.updated_weights,
        acknowledged: Boolean(res?.ok),
      })

      if (res?.ok) {
        void qc.invalidateQueries({ queryKey: queryKeys.weightsHistory })
      }
    },
    [pushActivity, qc, sessionId, track, userId],
  )

  return { track, signal, sessionId, userId }
}
