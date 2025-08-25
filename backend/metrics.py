from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

packets_total = Counter("netmon_packets_total", "Total packets captured", ["protocol"])
bytes_total = Counter("netmon_bytes_total", "Total bytes captured", ["protocol"])

pps_gauge = Gauge("netmon_pps", "Packets per second")
bps_gauge = Gauge("netmon_bps", "Bytes per second")
active_conns = Gauge("netmon_active_conns", "Unique source IPs in window")
ws_clients = Gauge("netmon_ws_clients", "Connected dashboard clients")
alerts_total = Counter("netmon_alerts_total", "Alerts fired", ["alert_type", "severity"])

pkt_size_hist = Histogram("netmon_pkt_size_bytes", "Packet size distribution", buckets=[64, 128, 256, 512, 1024, 1500, 4096, 9000],)

def update_from_snapshot(snap):
    pps_gauge.set(snap.pps)
    bps_gauge.set(snap.bps)
    active_conns.set(snap.active_conns)
    for proto, cnt in snap.protocol_counts.items():
        packets_total.labels(protocol=proto).inc(cnt)


def get_metrics():
    return generate_latest(), CONTENT_TYPE_LATEST
