import { useCallback, useEffect, useRef, useState } from 'react'
import { api, WS_URL } from '@/lib/api'
import type { TrafficSnapshot } from '@/lib/types'

export type TrafficPoint = TrafficSnapshot & { t: number; label: string }

export type ConnectionMode = 'connecting' | 'live' | 'polling' | 'offline'

const MAX_POINTS = 60
const POLL_MS = 2500
const MAX_BACKOFF = 15000

function toPoint(snapshot: TrafficSnapshot): TrafficPoint {
  const t = Date.now()
  return {
    ...snapshot,
    t,
    label: new Date(t).toLocaleTimeString('en-US', { minute: '2-digit', second: '2-digit' }),
  }
}

function isSnapshot(value: unknown): value is TrafficSnapshot {
  return Boolean(value) && typeof value === 'object' && 'rps' in (value as object)
}

/**
 * Live telemetry feed. Prefers the WebSocket; reconnects with exponential backoff and
 * transparently falls back to polling the REST snapshot whenever the socket is down,
 * so the control center keeps breathing even if the stream never comes up.
 */
export function useTrafficStream(enabled = true) {
  const [snapshot, setSnapshot] = useState<TrafficSnapshot | null>(null)
  const [series, setSeries] = useState<TrafficPoint[]>([])
  const [mode, setMode] = useState<ConnectionMode>('connecting')
  const [attempts, setAttempts] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<number>(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const aliveRef = useRef(true)

  const ingest = useCallback((next: TrafficSnapshot) => {
    setSnapshot(next)
    setSeries((prev) => [...prev, toPoint(next)].slice(-MAX_POINTS))
  }, [])

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    if (pollTimer.current) return
    const run = async () => {
      try {
        const data = await api.traffic()
        if (!aliveRef.current) return
        ingest(data)
        setMode((m) => (m === 'live' ? m : 'polling'))
        setLastError(null)
      } catch (err) {
        if (!aliveRef.current) return
        setMode((m) => (m === 'live' ? m : 'offline'))
        setLastError(err instanceof Error ? err.message : 'Telemetry unavailable')
      }
    }
    void run()
    pollTimer.current = setInterval(run, POLL_MS)
  }, [ingest])

  const connect = useCallback(() => {
    if (!aliveRef.current) return
    let socket: WebSocket
    try {
      socket = new WebSocket(WS_URL)
    } catch {
      startPolling()
      return
    }
    wsRef.current = socket
    setMode((m) => (m === 'offline' || m === 'polling' ? m : 'connecting'))

    socket.onopen = () => {
      if (!aliveRef.current) return
      retryRef.current = 0
      setAttempts(0)
      setMode('live')
      setLastError(null)
      stopPolling()
    }

    socket.onmessage = (event) => {
      if (!aliveRef.current) return
      try {
        const parsed = JSON.parse(event.data as string)
        if (isSnapshot(parsed)) {
          ingest(parsed)
          setMode('live')
        }
      } catch {
        /* ignore malformed frame */
      }
    }

    socket.onerror = () => {
      setLastError('Telemetry socket error')
    }

    socket.onclose = () => {
      if (!aliveRef.current) return
      wsRef.current = null
      setMode((m) => (m === 'offline' ? m : 'polling'))
      startPolling()
      const attempt = retryRef.current + 1
      retryRef.current = attempt
      setAttempts(attempt)
      const delay = Math.min(MAX_BACKOFF, 800 * 2 ** (attempt - 1)) + Math.random() * 400
      reconnectTimer.current = setTimeout(connect, delay)
    }
  }, [ingest, startPolling, stopPolling])

  useEffect(() => {
    if (!enabled) return
    aliveRef.current = true
    connect()
    return () => {
      aliveRef.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      stopPolling()
      const socket = wsRef.current
      wsRef.current = null
      if (socket) {
        socket.onclose = null
        socket.onerror = null
        socket.onmessage = null
        socket.onopen = null
        socket.close()
      }
    }
  }, [connect, enabled, stopPolling])

  const reconnectNow = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    retryRef.current = 0
    setAttempts(0)
    const socket = wsRef.current
    if (socket) {
      socket.onclose = null
      socket.close()
      wsRef.current = null
    }
    connect()
  }, [connect])

  return { snapshot, series, mode, attempts, lastError, reconnectNow }
}
