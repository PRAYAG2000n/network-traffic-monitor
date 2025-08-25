import { useState, useEffect, useRef } from "react"
import { useWebSocket } from "../hooks/useWebSocket"
import { TrafficSnapshot } from "../types"
import TrafficChart from "./TrafficChart"
import ProtocolBreakdown from "./ProtocolBreakdown"
import AlertHistory from "./AlertHistory"
import ThresholdConfig from "./ThresholdConfig"

const WS_URL = `ws://${window.location.hostname}:8000/ws/traffic`
const MAX_POINTS = 120 // 2 min of history in the chart

export default function Dashboard() {
  const { data: snapshot, connected } = useWebSocket<TrafficSnapshot>(WS_URL)
  const [history, setHistory] = useState<TrafficSnapshot[]>([])
  const histRef = useRef(history)
  histRef.current = history

  useEffect(() => {
    if (!snapshot) return
    setHistory((prev) => {
      const next = [...prev, snapshot]
      return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next
    })
  }, [snapshot])

  const fmtNum = (n: number) => {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K"
    return n.toFixed(0)
  }

  const statBox = (label: string, value: string, color: string) => (
    <div style={{
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      padding: "16px 20px",
      flex: 1,
      minWidth: 140,
    }}>
      <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: "24px", fontWeight: 700, color }}>{value}</div>
    </div>
  )

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "20px 16px" }}>
      {/* connection status */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: connected ? "#10b981" : "#ef4444",
        }} />
        <span style={{ fontSize: "13px", color: "#6b7280" }}>
          {connected ? "Live" : "Disconnected"}
        </span>
      </div>

      {/* stat cards */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        {statBox("Packets/sec", snapshot ? fmtNum(snapshot.pps) : "--", "#3b82f6")}
        {statBox("Bytes/sec", snapshot ? fmtNum(snapshot.bps) : "--", "#10b981")}
        {statBox("Active IPs", snapshot ? String(snapshot.active_conns) : "--", "#8b5cf6")}
        {statBox(
          "Protocols",
          snapshot ? String(Object.keys(snapshot.protocol_counts).length) : "--",
          "#f59e0b",
        )}
      </div>

      {/* charts row */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr auto",
        gap: 20,
        marginBottom: 24,
        alignItems: "start",
      }}>
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 600 }}>Traffic Over Time</h3>
          {history.length > 1 ? (
            <TrafficChart snapshots={history} width={680} height={280} />
          ) : (
            <p style={{ color: "#9ca3af", fontSize: "13px" }}>Waiting for data...</p>
          )}
        </div>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 600 }}>Protocol Breakdown</h3>
          {snapshot && Object.keys(snapshot.protocol_counts).length > 0 ? (
            <ProtocolBreakdown data={snapshot.protocol_counts} />
          ) : (
            <p style={{ color: "#9ca3af", fontSize: "13px" }}>No data</p>
          )}
        </div>
      </div>

      {/* top talkers */}
      {snapshot && snapshot.top_talkers.length > 0 && (
        <div style={{
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
        }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 600 }}>Top Talkers</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {snapshot.top_talkers.map((t) => (
              <div key={t.ip} style={{
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: 6,
                padding: "6px 12px",
                fontSize: "13px",
              }}>
                <span style={{ fontWeight: 600 }}>{t.ip}</span>
                <span style={{ color: "#6b7280", marginLeft: 6 }}>{t.packets} pkts</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* bottom row: alerts + thresholds */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
          <AlertHistory />
        </div>
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
          <ThresholdConfig />
        </div>
      </div>
    </div>
  )
}
