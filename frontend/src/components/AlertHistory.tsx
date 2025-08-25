import { useState, useEffect } from "react"
import { Alert } from "../types"

const API = `http://${window.location.hostname}:8000`
const PER_PAGE = 20

export default function AlertHistory() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const fetchAlerts = async (p: number) => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/alerts?page=${p}&per_page=${PER_PAGE}`)
      if (res.ok) setAlerts(await res.json())
    } catch (err) {
      console.error("failed to fetch alerts:", err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchAlerts(page)
    const interval = setInterval(() => fetchAlerts(page), 5000)
    return () => clearInterval(interval)
  }, [page])

  const severityColor = (s: string) => {
    if (s === "critical") return "#ef4444"
    if (s === "warning") return "#f59e0b"
    return "#6b7280"
  }

  return (
    <div>
      <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 600 }}>Alert History</h3>

      {loading && alerts.length === 0 && <p style={{ color: "#9ca3af" }}>Loading...</p>}

      {alerts.length === 0 && !loading && (
        <p style={{ color: "#9ca3af", fontSize: "13px" }}>No alerts yet</p>
      )}

      <div style={{ maxHeight: 300, overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #e5e7eb", textAlign: "left" }}>
              <th style={{ padding: "6px 8px" }}>Time</th>
              <th style={{ padding: "6px 8px" }}>Type</th>
              <th style={{ padding: "6px 8px" }}>Message</th>
              <th style={{ padding: "6px 8px" }}>Severity</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                <td style={{ padding: "6px 8px", whiteSpace: "nowrap" }}>
                  {new Date(a.timestamp).toLocaleTimeString()}
                </td>
                <td style={{ padding: "6px 8px" }}>{a.alert_type}</td>
                <td style={{ padding: "6px 8px" }}>{a.message}</td>
                <td style={{ padding: "6px 8px" }}>
                  <span style={{
                    color: severityColor(a.severity),
                    fontWeight: 600,
                    textTransform: "uppercase",
                    fontSize: "11px",
                  }}>
                    {a.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center" }}>
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          style={{ padding: "4px 12px", cursor: page === 1 ? "not-allowed" : "pointer" }}
        >
          Prev
        </button>
        <span style={{ fontSize: "13px", color: "#6b7280" }}>Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={alerts.length < PER_PAGE}
          style={{ padding: "4px 12px", cursor: alerts.length < PER_PAGE ? "not-allowed" : "pointer" }}
        >
          Next
        </button>
      </div>
    </div>
  )
}
