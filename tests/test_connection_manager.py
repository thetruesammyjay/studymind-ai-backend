"""Tests for WebSocket ConnectionManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websockets.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


def _make_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestConnect:
    @pytest.mark.asyncio
    async def test_accepts_websocket(self, manager):
        ws = _make_ws()
        await manager.connect("session-1", ws)
        ws.accept.assert_awaited_once()
        assert "session-1" in manager.active_connections
        assert ws in manager.active_connections["session-1"]

    @pytest.mark.asyncio
    async def test_multiple_connections_per_session(self, manager):
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("session-1", ws1)
        await manager.connect("session-1", ws2)
        assert len(manager.active_connections["session-1"]) == 2


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_removes_connection(self, manager):
        ws = _make_ws()
        await manager.connect("session-1", ws)
        manager.disconnect("session-1", ws)
        assert "session-1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_keeps_other_connections(self, manager):
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("session-1", ws1)
        await manager.connect("session-1", ws2)
        manager.disconnect("session-1", ws1)
        assert len(manager.active_connections["session-1"]) == 1
        assert ws2 in manager.active_connections["session-1"]

    def test_disconnect_nonexistent_session(self, manager):
        ws = _make_ws()
        # Should not raise
        manager.disconnect("nonexistent", ws)


class TestSendToSession:
    @pytest.mark.asyncio
    async def test_sends_to_all(self, manager):
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("session-1", ws1)
        await manager.connect("session-1", ws2)
        msg = {"type": "token", "content": "hello"}
        await manager.send_to_session("session-1", msg)
        ws1.send_json.assert_awaited_once_with(msg)
        ws2.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_no_op_for_nonexistent_session(self, manager):
        # Should not raise
        await manager.send_to_session("unknown", {"type": "test"})

    @pytest.mark.asyncio
    async def test_handles_send_failure(self, manager):
        ws1 = _make_ws()
        ws1.send_json = AsyncMock(side_effect=Exception("connection closed"))
        ws2 = _make_ws()
        await manager.connect("session-1", ws1)
        await manager.connect("session-1", ws2)
        # Should not raise, and ws2 should still receive
        await manager.send_to_session("session-1", {"type": "test"})
        ws2.send_json.assert_awaited_once()
