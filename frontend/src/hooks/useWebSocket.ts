import { useEffect, useRef, useState, useCallback } from "react"

const RECONNECT_DELAY = 3000
const MAX_RETRIES = 10

export function useWebSocket<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retriesRef.current = 0
    }

    ws.onmessage = (evt) => {
      try {
        setData(JSON.parse(evt.data))
      } catch {
        // bad payload, skip
      }
    }

    ws.onclose = () => {
      setConnected(false)
      if (retriesRef.current < MAX_RETRIES) {
        retriesRef.current++
        timerRef.current = setTimeout(connect, RECONNECT_DELAY)
      }
    }

    ws.onerror = () => ws.close()
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { data, connected }
}
