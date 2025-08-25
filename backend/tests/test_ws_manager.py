import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from ws_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect(manager, mock_ws):
    await manager.connect(mock_ws)
    assert manager.count == 1
    mock_ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect(manager, mock_ws):
    await manager.connect(mock_ws)
    manager.disconnect(mock_ws)
    assert manager.count == 0


@pytest.mark.asyncio
async def test_disconnect_nonexistent(manager, mock_ws):
    manager.disconnect(mock_ws)
    assert manager.count == 0


@pytest.mark.asyncio
async def test_broadcast(manager, mock_ws):
    await manager.connect(mock_ws)
    await manager.broadcast({"pps": 100})
    mock_ws.send_text.assert_awaited_once()
    sent = mock_ws.send_text.call_args[0][0]
    assert '"pps": 100' in sent


@pytest.mark.asyncio
async def test_broadcast_removes_dead_connections(manager):
    alive = AsyncMock()
    alive.accept = AsyncMock()
    alive.send_text = AsyncMock()

    dead = AsyncMock()
    dead.accept = AsyncMock()
    dead.send_text = AsyncMock(side_effect=Exception("connection lost"))

    await manager.connect(alive)
    await manager.connect(dead)
    assert manager.count == 2

    await manager.broadcast({"test": True})
    assert manager.count == 1  # dead one removed


@pytest.mark.asyncio
async def test_broadcast_multiple_clients(manager):
    clients = []
    for _ in range(5):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        await manager.connect(ws)
        clients.append(ws)

    await manager.broadcast({"data": "test"})
    for ws in clients:
        ws.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_count_property(manager, mock_ws):
    assert manager.count == 0
    await manager.connect(mock_ws)
    assert manager.count == 1
