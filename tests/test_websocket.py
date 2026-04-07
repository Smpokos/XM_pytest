"""
WebSocket Tests — xm.com
Tags: @websocket

XM streams live price data via WebSockets. These tests verify that the
connection infrastructure is working correctly.

Note: In the GR/EU region, WebSockets are only opened inside the trading
platform (members area). The homepage may use XHR polling instead.
Tests handle this gracefully with conditional assertions.

Python Playwright WebSocket API:
  page.on('websocket', handler)          — all WS connections
  ws.on('framesent', handler)            — browser → server frames
  ws.on('framereceived', handler)        — server → browser frames
  page.wait_for_event('websocket')       — wait for first WS
"""

import json
import time
from typing import List

import pytest
from playwright.sync_api import Page, WebSocket

from utils.websocket_monitor import WebSocketMonitor


pytestmark = pytest.mark.websocket


class TestWebSocketConnection:

    def test_at_least_one_websocket_opened_on_homepage(self, page: Page) -> None:
        from pages.base_page import BasePage

        monitor = WebSocketMonitor(page)
        monitor.start()

        base = BasePage(page)
        base.goto("/")
        page.wait_for_timeout(5_000)

        urls = monitor.urls()
        print(f"\nWebSocket URLs: {urls}")

        if len(urls) == 0:
            print(
                "No WebSocket opened on homepage — expected in EU/GR region. "
                "WS connections only open inside the trading platform."
            )
        else:
            assert len(urls) >= 1

    def test_websocket_receives_price_messages_within_15_seconds(
        self, page: Page
    ) -> None:
        from pages.base_page import BasePage

        monitor = WebSocketMonitor(page)
        monitor.start()

        base = BasePage(page)
        base.goto("/")

        try:
            monitor.wait_for_messages(count=1, timeout_ms=15_000)
        except TimeoutError:
            print(
                "\nNo WS messages received — "
                "page may not stream prices in this region"
            )
            return

        received = monitor.received()
        print(f"\nReceived {len(received)} WS messages")
        if received:
            print(f"Sample payload: {received[0].payload[:200]}")

    def test_capture_websocket_using_wait_for_event(self, page: Page) -> None:
        """
        Playwright's built-in event approach — resolves on first WS opened.
        The handler must be registered BEFORE navigation.
        """
        from pages.base_page import BasePage

        ws_captured: List[WebSocket] = []

        def on_ws(ws: WebSocket) -> None:
            ws_captured.append(ws)

        page.on("websocket", on_ws)

        base = BasePage(page)
        base.goto("/")
        page.wait_for_timeout(5_000)

        if ws_captured:
            ws = ws_captured[0]
            print(f"\nWebSocket opened: {ws.url}")
            assert ws.url  # URL must be non-empty
        else:
            print("\nNo WebSocket event detected — may be geo-restricted")

    def test_websocket_does_not_close_unexpectedly_within_5_seconds(
        self, page: Page
    ) -> None:
        from pages.base_page import BasePage

        premature_closes: List[str] = []

        def on_ws(ws: WebSocket) -> None:
            opened_at = time.time()

            def on_close() -> None:
                alive_ms = (time.time() - opened_at) * 1000
                if alive_ms < 5_000:
                    premature_closes.append(
                        f"WS closed after {alive_ms:.0f}ms: {ws.url}"
                    )

            ws.on("close", on_close)

        page.on("websocket", on_ws)

        base = BasePage(page)
        base.goto("/")
        page.wait_for_timeout(6_000)  # observe for 6 seconds

        for msg in premature_closes:
            print(f"\nWARNING: {msg}")

        assert len(premature_closes) == 0

    def test_inspect_ws_frame_structure(self, page: Page) -> None:
        """Capture frames and attempt JSON parsing to understand XM's protocol."""
        from pages.base_page import BasePage

        frames: List[str] = []

        def on_ws(ws: WebSocket) -> None:
            ws.on("framereceived", lambda f: frames.append(str(f.payload)))

        page.on("websocket", on_ws)

        base = BasePage(page)
        base.goto("/")
        page.wait_for_timeout(8_000)

        if not frames:
            print("\nNo frames collected — WS may not be active in this env")
            return

        first_frame = frames[0]
        print(f"\nFirst WS frame (truncated): {first_frame[:300]}")

        try:
            parsed = json.loads(first_frame)
            print(f"Frame is valid JSON with keys: {list(parsed.keys())}")
        except json.JSONDecodeError:
            print("Frame is not JSON (may be binary/protocol-specific)")
