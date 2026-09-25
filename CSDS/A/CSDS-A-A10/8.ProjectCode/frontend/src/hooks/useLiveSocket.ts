import { useEffect, useRef } from 'react'

export interface LiveEvent<T = unknown> {
  event: string
  payload: T
}

/**
 * Subscribes to MedFlow's live-update WebSocket and invokes `onEvent` for
 * every broadcast (queue changes, bed status, lab updates). Reconnects
 * automatically with backoff if the connection drops.
 */
export function useLiveSocket(onEvent: (evt: LiveEvent) => void) {
  const handlerRef = useRef(onEvent)
  handlerRef.current = onEvent

  useEffect(() => {
    let socket: WebSocket | null = null
    let retryDelay = 1000
    let closedByClient = false
    let retryTimer: ReturnType<typeof setTimeout> | undefined

    const connect = () => {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
      socket = new WebSocket(`${protocol}://${location.host}/ws/live`)

      socket.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data) as LiveEvent
          handlerRef.current(parsed)
        } catch {
          // ignore malformed frames
        }
      }

      socket.onclose = () => {
        if (closedByClient) return
        retryTimer = setTimeout(connect, retryDelay)
        retryDelay = Math.min(retryDelay * 1.5, 10000)
      }
    }

    connect()

    return () => {
      closedByClient = true
      if (retryTimer) clearTimeout(retryTimer)
      socket?.close()
    }
  }, [])
}
