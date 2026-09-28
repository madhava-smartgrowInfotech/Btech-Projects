import { useEffect, useRef, useState } from 'react'
import { wsUrl } from '../api'

/** Subscribes to live queue events for a hospital (0 = all). Calls onChange on every event. */
export default function useQueueSocket(hospitalId, onChange) {
  const [live, setLive] = useState(false)
  const cb = useRef(onChange)
  cb.current = onChange

  useEffect(() => {
    if (hospitalId === undefined || hospitalId === null) return
    let ws
    let ping
    let retry
    let closed = false
    const connect = () => {
      ws = new WebSocket(wsUrl(hospitalId))
      ws.onopen = () => {
        setLive(true)
        ping = setInterval(() => ws.readyState === 1 && ws.send('ping'), 25000)
      }
      ws.onmessage = (e) => {
        try {
          cb.current?.(JSON.parse(e.data))
        } catch {
          /* ignore malformed frames */
        }
      }
      ws.onclose = () => {
        setLive(false)
        clearInterval(ping)
        if (!closed) retry = setTimeout(connect, 2000)
      }
    }
    connect()
    return () => {
      closed = true
      clearInterval(ping)
      clearTimeout(retry)
      ws?.close()
    }
  }, [hospitalId])

  return live
}
