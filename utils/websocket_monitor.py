"""
WebSocketMonitor — captures and inspects WebSocket frames during a Playwright session.

XM uses WebSockets to stream live price data. This utility attaches to
Playwright's WebSocket events and records every frame for assertion.

Usage:
    monitor = WebSocketMonitor(page)
    monitor.start()
    page.goto("https://www.xm.com/")
    page.wait_for_timeout(5_000)
    assert len(monitor.received()) > 0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from playwright.sync_api import Page, WebSocket


@dataclass
class WsMessage:
    direction: str      # 'sent' | 'received'
    payload: str
    timestamp: float = field(default_factory=time.time)


class WebSocketMonitor:
    def __init__(self, page: Page) -> None:
        self.page = page
        self._messages: List[WsMessage] = []
        self._urls: List[str] = []

    def start(self) -> None:
        """Attach to all WebSocket events on the page."""

        def on_websocket(ws: WebSocket) -> None:
            self._urls.append(ws.url)

            def on_sent(payload: str) -> None:
                self._messages.append(
                    WsMessage(direction="sent", payload=str(payload))
                )

            def on_received(payload: str) -> None:
                self._messages.append(
                    WsMessage(direction="received", payload=str(payload))
                )

            ws.on("framesent", on_sent)
            ws.on("framereceived", on_received)
            ws.on("close", lambda: print(f"[WS] closed: {ws.url}"))

        self.page.on("websocket", on_websocket)

    # ── Accessors ──────────────────────────────────────────────────────

    def all(self) -> List[WsMessage]:
        return list(self._messages)

    def received(self) -> List[WsMessage]:
        return [m for m in self._messages if m.direction == "received"]

    def sent(self) -> List[WsMessage]:
        return [m for m in self._messages if m.direction == "sent"]

    def urls(self) -> List[str]:
        return list(self._urls)

    def find_received(self, pattern: str) -> Optional[WsMessage]:
        """Return first received message whose payload contains pattern."""
        return next(
            (m for m in self.received() if pattern in m.payload), None
        )

    def clear(self) -> None:
        self._messages.clear()

    def wait_for_messages(
        self, count: int = 1, timeout_ms: int = 15_000
    ) -> None:
        """
        Poll until at least `count` received messages are captured.
        Raises TimeoutError if not enough messages arrive in time.
        """
        deadline = time.time() + timeout_ms / 1000
        while time.time() < deadline:
            if len(self.received()) >= count:
                return
            time.sleep(0.3)
        raise TimeoutError(
            f"Expected {count} WS messages, got {len(self.received())}"
        )
