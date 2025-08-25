import pytest
from unittest.mock import MagicMock, patch
from collections import deque

from sniffer import PacketSniffer
from models import TrafficSnapshot, Alert, ThresholdConfig, Protocol


@pytest.fixture
def snf():
    s = PacketSniffer(iface="lo", history_len=60)
    return s


def test_init_defaults(snf):
    assert snf.running is False
    assert snf.iface == "lo"
    assert len(snf.packets) == 0
    assert len(snf.snapshots) == 0
    assert len(snf.alerts) == 0


def test_get_protocol_tcp(snf):
    pkt = MagicMock()
    pkt.haslayer = lambda x: x.__name__ == "TCP"
    mock_tcp = MagicMock()
    mock_tcp.sport = 12345
    mock_tcp.dport = 8080
    pkt.__getitem__ = lambda self, x: mock_tcp
    assert snf._get_protocol(pkt) == Protocol.TCP


def test_get_protocol_http(snf):
    pkt = MagicMock()
    pkt.haslayer = lambda x: x.__name__ == "TCP"
    mock_tcp = MagicMock()
    mock_tcp.sport = 80
    mock_tcp.dport = 50000
    pkt.__getitem__ = lambda self, x: mock_tcp
    assert snf._get_protocol(pkt) == Protocol.HTTP


def test_get_protocol_https(snf):
    pkt = MagicMock()
    pkt.haslayer = lambda x: x.__name__ == "TCP"
    mock_tcp = MagicMock()
    mock_tcp.sport = 443
    mock_tcp.dport = 50000
    pkt.__getitem__ = lambda self, x: mock_tcp
    assert snf._get_protocol(pkt) == Protocol.HTTPS


def test_get_protocol_dns(snf):
    pkt = MagicMock()
    pkt.haslayer = lambda x: x.__name__ == "DNS"
    assert snf._get_protocol(pkt) == Protocol.DNS


def test_get_protocol_udp(snf):
    pkt = MagicMock()
    def has(x):
        return x.__name__ == "UDP"
    pkt.haslayer = has
    assert snf._get_protocol(pkt) == Protocol.UDP


def test_get_protocol_icmp(snf):
    pkt = MagicMock()
    def has(x):
        return x.__name__ == "ICMP"
    pkt.haslayer = has
    assert snf._get_protocol(pkt) == Protocol.ICMP


def test_latest_empty(snf):
    assert snf.latest() is None


def test_latest_returns_last(snf):
    s1 = TrafficSnapshot(pps=10)
    s2 = TrafficSnapshot(pps=20)
    snf.snapshots.append(s1)
    snf.snapshots.append(s2)
    assert snf.latest().pps == 20


def test_recent_snapshots(snf):
    for i in range(10):
        snf.snapshots.append(TrafficSnapshot(pps=float(i)))
    result = snf.recent_snapshots(n=3)
    assert len(result) == 3
    assert result[0].pps == 7.0  # last 3: 7, 8, 9


def test_recent_snapshots_fewer_than_n(snf):
    snf.snapshots.append(TrafficSnapshot(pps=1))
    result = snf.recent_snapshots(n=100)
    assert len(result) == 1


def test_get_alerts_empty(snf):
    assert snf.get_alerts() == []


def test_get_alerts_reversed(snf):
    for i in range(5):
        snf.alerts.append(Alert(
            id=str(i), alert_type="test", message=f"msg {i}",
        ))
    result = snf.get_alerts(page=1, per_page=5)
    assert result[0].id == "4"  # most recent first


def test_get_alerts_pagination(snf):
    for i in range(30):
        snf.alerts.append(Alert(
            id=str(i), alert_type="test", message=f"msg {i}",
        ))
    page1 = snf.get_alerts(page=1, per_page=10)
    page2 = snf.get_alerts(page=2, per_page=10)
    assert len(page1) == 10
    assert len(page2) == 10
    assert page1[0].id != page2[0].id


def test_set_thresholds(snf):
    cfg = ThresholdConfig(max_pps=999, max_bps=888, max_conns_per_ip=77)
    snf.set_thresholds(cfg)
    assert snf.thresholds.max_pps == 999


def test_check_alerts_pps_exceeded(snf):
    snf.thresholds = ThresholdConfig(max_pps=100, max_bps=999999)
    snap = TrafficSnapshot(pps=200, bps=100)
    snf._check_alerts(snap)
    assert len(snf.alerts) == 1
    assert snf.alerts[0].severity == "critical"


def test_check_alerts_bps_exceeded(snf):
    snf.thresholds = ThresholdConfig(max_pps=999999, max_bps=100)
    snap = TrafficSnapshot(pps=10, bps=200)
    snf._check_alerts(snap)
    assert len(snf.alerts) == 1
    assert "BPS" in snf.alerts[0].message


def test_check_alerts_nothing_exceeded(snf):
    snf.thresholds = ThresholdConfig(max_pps=999999, max_bps=999999)
    snap = TrafficSnapshot(pps=10, bps=100)
    snf._check_alerts(snap)
    assert len(snf.alerts) == 0


def test_start_stop(snf):
    with patch("sniffer.sniff"):
        snf.start()
        assert snf.running is True
        snf.stop()
        assert snf.running is False
