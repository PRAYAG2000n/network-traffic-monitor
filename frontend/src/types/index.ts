export interface TrafficSnapshot {
  timestamp: string
  pps: number
  bps: number
  protocol_counts: Record<string, number>
  top_talkers: { ip: string; packets: number }[]
  active_conns: number
}

export interface Alert {
  id: string
  timestamp: string
  alert_type: string
  message: string
  severity: string
  resolved: boolean
}

export interface ThresholdConfig {
  max_pps: number
  max_bps: number
  max_conns_per_ip: number
}
