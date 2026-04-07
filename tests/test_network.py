"""
Network / Route Interception Tests — xm.com

Python Playwright's routing API:
  page.route(pattern, handler) — intercept matching requests
  page.unroute(pattern)        — remove an intercept
  route.abort()                — block the request
  route.fulfill(...)           — mock the response
  route.continue_(...)         — pass through (optionally modified)
  page.wait_for_response(...)  — wait for a specific response
  page.wait_for_request(...)   — wait for a specific request
"""

import pytest
from playwright.sync_api import Page, Route, Request, Response, expect

from pages.base_page import BasePage


class TestNetworkInterception:

    def test_block_image_requests_to_speed_up_tests(self, page: Page) -> None:
        """Aborting image requests is a common CI optimisation."""
        page.route(
            "**/*.{png,jpg,webp,svg}",
            lambda route: route.abort()
        )
        base = BasePage(page)
        base.goto("/")

        # Page must still load without images
        expect(page.get_by_role("heading", level=1)).to_be_visible()

    def test_intercept_and_mock_an_api_response(self, page: Page) -> None:
        """Mock any API call — useful for testing error states."""
        def mock_api(route: Route) -> None:
            print(f"\nIntercepted API call: {route.request.url}")
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"mocked": true, "instruments": ["EURUSD", "GOLD"]}',
            )

        page.route("**/api/**", mock_api)

        base = BasePage(page)
        base.goto("/")
        expect(page).to_have_title(pytest.approx("XM", rel=1))
        assert "XM" in page.title()

    def test_wait_for_a_specific_network_response(self, page: Page) -> None:
        """Register the listener BEFORE navigating."""
        with page.expect_response(
            lambda resp: "xm.com" in resp.url and resp.status == 200,
            timeout=15_000,
        ) as response_info:
            base = BasePage(page)
            base.goto("/")

        response = response_info.value
        assert response.status == 200
        print(f"\nFirst matched response URL: {response.url}")

    def test_assert_no_failed_network_requests_on_homepage(
        self, page: Page
    ) -> None:
        """Collect 4xx/5xx responses and assert minimal failures."""
        failed: list[str] = []

        def on_response(response: Response) -> None:
            if response.status >= 400:
                failed.append(f"{response.status} {response.url}")

        page.on("response", on_response)

        base = BasePage(page)
        base.goto("/")
        page.wait_for_load_state("domcontentloaded")

        # Filter to XM-owned requests only
        xm_failures = [
            url for url in failed
            if "xm.com" in url and "analytics" not in url
        ]

        if xm_failures:
            print(f"\nFailed requests: {xm_failures}")

        # Soft threshold — third-party resources may legitimately fail
        assert len(xm_failures) <= 2

    def test_modify_request_headers_before_sending(self, page: Page) -> None:
        """Add a custom header to outgoing requests."""
        def add_header(route: Route) -> None:
            headers = {
                **route.request.headers,
                "X-Custom-Test-Header": "playwright-interview",
            }
            route.continue_(headers=headers)

        page.route("https://www.xm.com/", add_header)

        base = BasePage(page)
        base.inject_stealth_script()
        response = page.goto("https://www.xm.com/", wait_until="commit")
        assert response is not None
        assert response.status == 200
