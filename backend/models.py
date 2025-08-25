from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class Protocol(str, Enum):
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    DNS = "DNS"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    ARP = "ARP"
    OTHER = "OTHER"


class PacketInfo(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Protocol
    size: int
    flags: Optional[str] = None


class TrafficSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pps: float = 0.0
    bps: float = 0.0
    protocol_counts: dict[str, int] = {}
    top_talkers: list[dict] = []
    active_conns: int = 0


class Alert(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alert_type: str
    message: str
    severity: str = "warning"
    resolved: bool = False


class ThresholdConfig(BaseModel):
    max_pps: float = 5000.0
    max_bps: float = 10_000_000.0
    max_conns_per_ip: int = 100
