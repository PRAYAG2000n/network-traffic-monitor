import { useState, useEffect } from "react"
import { ThresholdConfig as TConfig } from "../types"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default function ThresholdConfig() {
  const [config, setConfig] = useState<TConfig>({
    max_pps: 5000,
    max_bps: 10000000,
    max_conns_per_ip: 100,
  })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState("")

  useEffect(() => {
    fetch(`${API}/api/thresholds`)
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => {})
  }, [])

  const save = async () => {
    setSaving(true)
    setMsg("")
    try {
      const res = await fetch(`${API}/api/thresholds`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })
      if (res.ok) {
        setMsg("Saved")
        setTimeout(() => setMsg(""), 2000)
      } else {
        setMsg("Failed to save")
      }
    } catch {
      setMsg("Network error")
    }
    setSaving(false)
  }

  const inputStyle = {
    width: "100%",
    padding: "6px 8px",
    border: "1px solid #d1d5db",
    borderRadius: 4,
    fontSize: "13px",
  }

  const labelStyle = {
    display: "block",
    marginBottom: 4,
    fontSize: "12px",
    fontWeight: 600 as const,
    color: "#374151",
  }

  return (
    <div>
      <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 600 }}>Thresholds</h3>

      <div style={{ display: "flex", flexDirection: "column" as const, gap: 12 }}>
        <div>
          <label style={labelStyle}>Max Packets/sec</label>
          <input
            type="number"
            value={config.max_pps}
            onChange={(e) => setConfig({ ...config, max_pps: +e.target.value })}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>Max Bytes/sec</label>
          <input
            type="number"
            value={config.max_bps}
            onChange={(e) => setConfig({ ...config, max_bps: +e.target.value })}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>Max Connections per IP</label>
          <input
            type="number"
            value={config.max_conns_per_ip}
            onChange={(e) => setConfig({ ...config, max_conns_per_ip: +e.target.value })}
            style={inputStyle}
          />
        </div>

        <button
          onClick={save}
          disabled={saving}
          style={{
            padding: "8px 16px",
            background: "#3b82f6",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: saving ? "not-allowed" : "pointer",
            fontSize: "13px",
          }}
        >
          {saving ? "Saving..." : "Save"}
        </button>

        {msg && <span style={{ fontSize: "12px", color: msg === "Saved" ? "#10b981" : "#ef4444" }}>{msg}</span>}
      </div>
    </div>
  )
}
