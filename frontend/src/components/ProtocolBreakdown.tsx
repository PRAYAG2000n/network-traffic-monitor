import { useEffect, useRef } from "react"
import * as d3 from "d3"

interface Props {
  data: Record<string, number>
  size?: number
}

const COLORS: Record<string, string> = {
  TCP: "#3b82f6",
  UDP: "#10b981",
  HTTP: "#f59e0b",
  HTTPS: "#8b5cf6",
  DNS: "#ec4899",
  ICMP: "#6366f1",
  ARP: "#14b8a6",
  OTHER: "#9ca3af",
}

export default function ProtocolBreakdown({ data, size = 260 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return
    const entries = Object.entries(data).filter(([, v]) => v > 0)
    if (entries.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const radius = size / 2 - 10
    const g = svg.append("g").attr("transform", `translate(${size / 2},${size / 2})`)

    const pie = d3.pie<[string, number]>().value((d) => d[1]).sort(null)
    const arc = d3.arc<d3.PieArcDatum<[string, number]>>().innerRadius(radius * 0.55).outerRadius(radius)

    const arcs = g.selectAll("path").data(pie(entries)).join("path")
    arcs
      .attr("d", arc)
      .attr("fill", (d) => COLORS[d.data[0]] || "#9ca3af")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)

    // labels
    const labelArc = d3.arc<d3.PieArcDatum<[string, number]>>().innerRadius(radius * 0.8).outerRadius(radius * 0.8)
    g.selectAll("text")
      .data(pie(entries))
      .join("text")
      .attr("transform", (d) => `translate(${labelArc.centroid(d)})`)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#374151")
      .text((d) => {
        const total = entries.reduce((s, [, v]) => s + v, 0)
        const pct = ((d.data[1] / total) * 100).toFixed(0)
        return +pct > 4 ? `${d.data[0]} ${pct}%` : ""
      })
  }, [data, size])

  return <svg ref={svgRef} width={size} height={size} />
}
