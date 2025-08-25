import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models import ThresholdConfig
from sniffer import PacketSniffer
from ws_manager import ConnectionManager
from metrics import update_from_snapshot, get_metrics, ws_clients

IFACE = os.getenv("SNIFF_INTERFACE", None)

sniffer = PacketSniffer(iface=IFACE)
ws_mgr = ConnectionManager()


async def _push_loop():
    """Push snapshots to dashboard clients every second."""
    while True:
        await asyncio.sleep(1.0)
        snap = sniffer.latest()
        if not snap:
            continue
        update_from_snapshot(snap)
        ws_clients.set(ws_mgr.count)
        await ws_mgr.broadcast(snap.model_dump())


@asynccontextmanager
async def lifespan(app: FastAPI):
    sniffer.start()
    task = asyncio.create_task(_push_loop())
    yield
    task.cancel()
    sniffer.stop()


app = FastAPI(title="Network Traffic Monitor", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

@app.get("/api/snapshots")
def snapshots(last_n: int = Query(default=60, ge=1, le=3600)):
    return sniffer.recent_snapshots(n=last_n)


@app.get("/api/alerts")
def alerts(page: int = Query(default=1, ge=1), per_page: int = Query(default=20, ge=1, le=100)):
    return sniffer.get_alerts(page=page, per_page=per_page)


@app.get("/api/thresholds")
def get_thresholds():
    return sniffer.thresholds


@app.put("/api/thresholds")
def put_thresholds(config: ThresholdConfig):
    sniffer.set_thresholds(config)
    return sniffer.thresholds


@app.get("/api/status")
def status():
    return {
        "running": sniffer.running,
        "clients": ws_mgr.count,
        "snapshots": len(sniffer.snapshots),
        "alerts": len(sniffer.alerts),
    }

# TODO: might want to move this behind auth or a separate port
@app.get("/metrics")
def prom_metrics():
    data, ctype = get_metrics()
    return Response(content=data, media_type=ctype)


@app.websocket("/ws/traffic")
async def ws_traffic(ws: WebSocket):
    await ws_mgr.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_mgr.disconnect(ws)
