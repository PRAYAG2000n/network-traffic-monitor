import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from main import app, sniffer
from models import TrafficSnapshot, Alert, ThresholdConfig


client = TestClient(app)


#fixtures
@pytest.fixture(autouse=True)
def reset_sniffer():
    """Reset sniffer state between tests."""
    sniffer.alerts.clear()
    sniffer.snapshots.clear()
    sniffer.thresholds = ThresholdConfig()
    yield


@pytest.fixture
def sample_snapshot():
    return TrafficSnapshot(
        pps=150.0,
        bps=24000.0,
        protocol_counts={"TCP": 80, "UDP": 40, "DNS": 30},
        top_talkers=[
            {"ip": "192.168.1.10", "packets": 50},
            {"ip": "10.0.0.5", "packets": 30},
        ],
        active_conns=12,
    )


@pytest.fixture
def sample_alerts():
    return [
        Alert(
            id="abc123",
            alert_type="high_pps",
            message="PPS 6000 > threshold 5000",
            severity="critical",
        ),
        Alert(
            id="def456",
            alert_type="high_bps",
            message="BPS 15000000 > threshold 10000000",
            severity="critical",
        ),
    ]


#api-status
def test_status_endpoint():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "running" in data
    assert "clients" in data
    assert "snapshots" in data
    assert "alerts" in data


#api-snapshots
def test_snapshots_empty():
    resp = client.get("/api/snapshots")
    assert resp.status_code == 200
    assert resp.json() == []


def test_snapshots_returns_data(sample_snapshot):
    sniffer.snapshots.append(sample_snapshot)
    resp = client.get("/api/snapshots?last_n=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["pps"] == 150.0
    assert data[0]["protocol_counts"]["TCP"] == 80


def test_snapshots_respects_last_n(sample_snapshot):
    for _ in range(5):
        sniffer.snapshots.append(sample_snapshot)
    resp = client.get("/api/snapshots?last_n=3")
    data = resp.json()
    assert len(data) == 3


def test_snapshots_last_n_validation():
    resp = client.get("/api/snapshots?last_n=0")
    assert resp.status_code == 422

    resp = client.get("/api/snapshots?last_n=5000")
    assert resp.status_code == 422


#api-alerts
def test_alerts_empty():
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_alerts_returns_data(sample_alerts):
    for a in sample_alerts:
        sniffer.alerts.append(a)
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["alert_type"] == "high_bps"  # reversed order


def test_alerts_pagination(sample_alerts):
    for i in range(25):
        sniffer.alerts.append(Alert(
            id=f"alert_{i}",
            alert_type="high_pps",
            message=f"test alert {i}",
            severity="warning",
        ))
    resp = client.get("/api/alerts?page=1&per_page=10")
    assert len(resp.json()) == 10

    resp = client.get("/api/alerts?page=2&per_page=10")
    assert len(resp.json()) == 10

    resp = client.get("/api/alerts?page=3&per_page=10")
    assert len(resp.json()) == 5


def test_alerts_page_validation():
    resp = client.get("/api/alerts?page=0")
    assert resp.status_code == 422

    resp = client.get("/api/alerts?per_page=200")
    assert resp.status_code == 422


#api thresholds
def test_get_thresholds_defaults():
    resp = client.get("/api/thresholds")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_pps"] == 5000.0
    assert data["max_bps"] == 10_000_000.0
    assert data["max_conns_per_ip"] == 100


def test_put_thresholds():
    new_config = {"max_pps": 8000, "max_bps": 20000000, "max_conns_per_ip": 200}
    resp = client.put("/api/thresholds", json=new_config)
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_pps"] == 8000.0
    assert data["max_conns_per_ip"] == 200

    resp = client.get("/api/thresholds")   # verify it persists
    assert resp.json()["max_pps"] == 8000.0


def test_put_thresholds_partial():
    resp = client.put("/api/thresholds", json={"max_pps": 9999})
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_pps"] == 9999
    assert data["max_bps"] == 10000000  #defaults for unset fields


#metrics
def test_prometheus_metrics():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"netmon_pps" in resp.content
    assert b"netmon_bps" in resp.content


#websocket
def test_websocket_connects():
    with client.websocket_connect("/ws/traffic") as ws:
        assert ws is not None  # connection should be accepted


def test_sniffer_threshold_check():
    sniffer.thresholds = ThresholdConfig(max_pps=100, max_bps=1000, max_conns_per_ip=10)
    snap = TrafficSnapshot(pps=200, bps=500, active_conns=5)
    sniffer._check_alerts(snap)
    assert len(sniffer.alerts) == 1
    assert sniffer.alerts[0].alert_type == "high_pps"


def test_sniffer_threshold_both_exceeded():
    sniffer.thresholds = ThresholdConfig(max_pps=100, max_bps=1000, max_conns_per_ip=10)
    snap = TrafficSnapshot(pps=200, bps=2000, active_conns=5)
    sniffer._check_alerts(snap)
    assert len(sniffer.alerts) == 2


def test_sniffer_threshold_none_exceeded():
    sniffer.thresholds = ThresholdConfig(max_pps=1000, max_bps=100000, max_conns_per_ip=50)
    snap = TrafficSnapshot(pps=50, bps=500, active_conns=3)
    sniffer._check_alerts(snap)
    assert len(sniffer.alerts) == 0


def test_sniffer_get_latest_empty():
    assert sniffer.latest() is None


def test_sniffer_get_latest(sample_snapshot):
    sniffer.snapshots.append(sample_snapshot)
    result = sniffer.latest()
    assert result.pps == 150.0


def test_sniffer_recent_snapshots(sample_snapshot):
    for _ in range(10):
        sniffer.snapshots.append(sample_snapshot)
    result = sniffer.recent_snapshots(n=5)
    assert len(result) == 5


def test_sniffer_set_thresholds():
    new = ThresholdConfig(max_pps=999, max_bps=888, max_conns_per_ip=77)
    sniffer.set_thresholds(new)
    assert sniffer.thresholds.max_pps == 999
    assert sniffer.thresholds.max_bps == 888
