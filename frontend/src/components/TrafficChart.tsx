import { useEffect, useRef } from "react"
import * as d3 from "d3"
import { TrafficSnapshot } from "../types"

interface Props {
  snapshots: TrafficSnapshot[]
  width?: number
  height?: number
}

const MARGIN = { top: 20, right: 60, bottom: 30, left: 60 }

export default function TrafficChart({ snapshots, width = 700, height = 300 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || snapshots.length < 2) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const w = width - MARGIN.left - MARGIN.right
    const h = height - MARGIN.top - MARGIN.bottom

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`)

    const parseTime = (s: string) => new Date(s)
    const times = snapshots.map((d) => parseTime(d.timestamp))

    // x axis
    const x = d3.scaleTime().domain(d3.extent(times) as [Date, Date]).range([0, w])
    g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(6))

    // left y: packets/s
    const yPps = d3
      .scaleLinear()
      .domain([0, d3.max(snapshots, (d) => d.pps) || 100])
      .nice()
      .range([h, 0])
    g.append("g").call(d3.axisLeft(yPps).ticks(5))
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -45)
      .attr("x", -h / 2)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#6b7280")
      .text("Packets/s")

    // right y: bytes/s
    const yBps = d3
      .scaleLinear()
      .domain([0, d3.max(snapshots, (d) => d.bps) || 1000])
      .nice()
      .range([h, 0])
    g.append("g").attr("transform", `translate(${w},0)`).call(d3.axisRight(yBps).ticks(5))
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", w + 50)
      .attr("x", -h / 2)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#6b7280")
      .text("Bytes/s")

    // pps line
    const ppsLine = d3
      .line<TrafficSnapshot>()
      .x((_, i) => x(times[i]))
      .y((d) => yPps(d.pps))
      .curve(d3.curveMonotoneX)

    g.append("path")
      .datum(snapshots)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2)
      .attr("d", ppsLine)

    // bps line
    const bpsLine = d3
      .line<TrafficSnapshot>()
      .x((_, i) => x(times[i]))
      .y((d) => yBps(d.bps))
      .curve(d3.curveMonotoneX)

    g.append("path")
      .datum(snapshots)
      .attr("fill", "none")
      .attr("stroke", "#10b981")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,3")
      .attr("d", bpsLine)

    // legend
    const legend = g.append("g").attr("transform", `translate(${w - 120}, 0)`)
    legend.append("line").attr("x1", 0).attr("x2", 20).attr("y1", 0).attr("y2", 0).attr("stroke", "#3b82f6").attr("stroke-width", 2)
    legend.append("text").attr("x", 25).attr("y", 4).attr("font-size", "11px").attr("fill", "#374151").text("PPS")
    legend.append("line").attr("x1", 0).attr("x2", 20).attr("y1", 18).attr("y2", 18).attr("stroke", "#10b981").attr("stroke-width", 2).attr("stroke-dasharray", "5,3")
    legend.append("text").attr("x", 25).attr("y", 22).attr("font-size", "11px").attr("fill", "#374151").text("BPS")
  }, [snapshots, width, height])

  return <svg ref={svgRef} width={width} height={height} />
}
