import pytest
from datetime import datetime
from models import PacketInfo, Protocol, TrafficSnapshot, Alert, ThresholdConfig


def test_packet_info_with_ports():
    pkt = PacketInfo(
        src_ip="192.168.1.1",
        dst_ip="10.0.0.1",
        src_port=443,
        dst_port=52000,
        protocol=Protocol.HTTPS,
        size=1500,
        flags="SA",
    )
    assert pkt.src_port == 443
    assert pkt.flags == "SA"
    assert pkt.protocol == Protocol.HTTPS


def test_packet_info_without_ports():
    pkt = PacketInfo(
        src_ip="192.168.1.1",
        dst_ip="10.0.0.1",
        protocol=Protocol.ICMP,
        size=64,
    )
    assert pkt.src_port is None
    assert pkt.dst_port is None
    assert pkt.flags is None


def test_packet_info_timestamp_auto():
    pkt = PacketInfo(
        src_ip="1.1.1.1", dst_ip="2.2.2.2",
        protocol=Protocol.DNS, size=120,
    )
    assert isinstance(pkt.timestamp, datetime)


def test_traffic_snapshot_defaults():
    snap = TrafficSnapshot()
    assert snap.pps == 0.0
    assert snap.bps == 0.0
    assert snap.protocol_counts == {}
    assert snap.top_talkers == []
    assert snap.active_conns == 0


def test_traffic_snapshot_with_data():
    snap = TrafficSnapshot(
        pps=500.0,
        bps=100000.0,
        protocol_counts={"TCP": 300, "UDP": 200},
        top_talkers=[{"ip": "10.0.0.1", "packets": 100}],
        active_conns=25,
    )
    assert snap.pps == 500.0
    assert len(snap.protocol_counts) == 2
    assert snap.top_talkers[0]["ip"] == "10.0.0.1"


def test_alert_creation():
    alert = Alert(
        id="test123",
        alert_type="high_pps",
        message="PPS exceeded",
        severity="critical",
    )
    assert alert.resolved is False
    assert alert.severity == "critical"
    assert isinstance(alert.timestamp, datetime)


def test_alert_default_severity():
    alert = Alert(
        id="x", alert_type="test", message="msg",
    )
    assert alert.severity == "warning"


def test_threshold_config_defaults():
    cfg = ThresholdConfig()
    assert cfg.max_pps == 5000.0
    assert cfg.max_bps == 10_000_000.0
    assert cfg.max_conns_per_ip == 100


def test_threshold_config_custom():
    cfg = ThresholdConfig(max_pps=100, max_bps=500, max_conns_per_ip=5)
    assert cfg.max_pps == 100
    assert cfg.max_bps == 500


def test_protocol_enum_values():
    assert Protocol.TCP.value == "TCP"
    assert Protocol.HTTPS.value == "HTTPS"
    assert Protocol.OTHER.value == "OTHER"


def test_protocol_enum_membership():
    assert "TCP" in [p.value for p in Protocol]
    assert "INVALID" not in [p.value for p in Protocol]
