import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime
from scapy.all import sniff, IP, TCP, UDP, ICMP, DNS, ARP
from models import PacketInfo, Protocol, TrafficSnapshot, Alert, ThresholdConfig


class PacketSniffer:
    def __init__(self, iface=None, history_len=3600):
        self.iface = iface
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
        self.packets = deque(maxlen=100_000)
        self.snapshots = deque(maxlen=history_len)
        self.alerts = deque(maxlen=1000)
        self.thresholds = ThresholdConfig()

        # per-second accumulators, reset every snapshot tick
        self._pkt_count = 0
        self._byte_count = 0
        self._proto_counts = defaultdict(int)
        self._ip_hits = defaultdict(int)

    def _get_protocol(self, pkt):
        if pkt.haslayer(DNS):
            return Protocol.DNS
        if pkt.haslayer(ARP):
            return Protocol.ARP
        if pkt.haslayer(ICMP):
            return Protocol.ICMP
        if pkt.haslayer(TCP):
            sp, dp = pkt[TCP].sport, pkt[TCP].dport
            if 80 in (sp, dp):
                return Protocol.HTTP
            if 443 in (sp, dp):
                return Protocol.HTTPS
            return Protocol.TCP
        if pkt.haslayer(UDP):
            return Protocol.UDP
        return Protocol.OTHER

    def _handle_packet(self, pkt):
        if not pkt.haslayer(IP) and not pkt.haslayer(ARP):
            return

        proto = self._get_protocol(pkt)
        src = pkt[IP].src if pkt.haslayer(IP) else "N/A"
        dst = pkt[IP].dst if pkt.haslayer(IP) else "N/A"

        sport = dport = None
        flags = None
        if pkt.haslayer(TCP):
            sport, dport = pkt[TCP].sport, pkt[TCP].dport
            flags = str(pkt[TCP].flags)
        elif pkt.haslayer(UDP):
            sport, dport = pkt[UDP].sport, pkt[UDP].dport

        info = PacketInfo(src_ip=src, dst_ip=dst, src_port=sport, dst_port=dport, protocol=proto, size=len(pkt), flags=flags,)
        with self._lock:
            self.packets.append(info)
            self._pkt_count += 1
            self._byte_count += info.size
            self._proto_counts[proto.value] += 1
            self._ip_hits[src] += 1

    def _snapshot_loop(self):
        while self.running:
            time.sleep(1.0)
            with self._lock:
                sorted_ips = sorted(self._ip_hits.items(), key=lambda x: x[1], reverse=True)[:10] # grab top 10 talkers
                snap = TrafficSnapshot(pps=self._pkt_count, bps=self._byte_count, protocol_counts=dict(self._proto_counts), top_talkers=[{"ip": ip, "packets": n} for ip, n in sorted_ips], active_conns=len(self._ip_hits),)
                self.snapshots.append(snap)
                self._check_alerts(snap)

                # reset
                self._pkt_count = 0
                self._byte_count = 0
                self._proto_counts.clear()
                self._ip_hits.clear()

    def _check_alerts(self, snap):
        if snap.pps > self.thresholds.max_pps:
            self.alerts.append(Alert(
                id=uuid.uuid4().hex[:12],
                alert_type="high_pps",
                message=f"PPS {snap.pps:.0f} > threshold {self.thresholds.max_pps:.0f}",
                severity="critical",
            ))
        if snap.bps > self.thresholds.max_bps:
            self.alerts.append(Alert(
                id=uuid.uuid4().hex[:12],
                alert_type="high_bps",
                message=f"BPS {snap.bps:.0f} > threshold {self.thresholds.max_bps:.0f}",
                severity="critical",
            ))

    def start(self):
        if self.running:
            return
        self.running = True

        threading.Thread(target=self._snapshot_loop, daemon=True).start()
        self._thread = threading.Thread(target=self._run_capture, daemon=True)
        self._thread.start()

    def _run_capture(self):
        sniff(
            iface=self.iface,
            prn=self._handle_packet,
            store=False,
            stop_filter=lambda _: not self.running,
        )

    def stop(self):
        self.running = False

    def latest(self):
        with self._lock:
            return self.snapshots[-1] if self.snapshots else None

    def recent_snapshots(self, n=60):
        with self._lock:
            return list(self.snapshots)[-n:]

    def get_alerts(self, page=1, per_page=20):
        items = list(reversed(self.alerts))
        start = (page - 1) * per_page
        return items[start:start + per_page]

    def set_thresholds(self, config):
        with self._lock:
            self.thresholds = config
