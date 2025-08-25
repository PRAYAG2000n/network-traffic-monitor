import Dashboard from "./components/Dashboard"

function App() {
  return (
    <div style={{ background: "#f3f4f6", minHeight: "100vh" }}>
      <header style={{
        background: "#fff",
        borderBottom: "1px solid #e5e7eb",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <h1 style={{ margin: 0, fontSize: "18px", fontWeight: 700 }}>
          Network Traffic Monitor
        </h1>
        <span style={{ fontSize: "12px", color: "#9ca3af" }}>v1.0</span>
      </header>
      <Dashboard />
    </div>
  )
}

export default App
