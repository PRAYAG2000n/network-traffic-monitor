import json
from datetime import datetime
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        def _serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"not serializable: {type(obj)}")

        msg = json.dumps(data, default=_serialize)
        stale = []
        for conn in self.connections:
            try:
                await conn.send_text(msg)
            except Exception:
                stale.append(conn)

        for c in stale:
            self.disconnect(c)

    @property
    def count(self):
        return len(self.connections)
