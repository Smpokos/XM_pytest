"""
NavigationPage — exercises XM's main nav dropdowns and URL routing.

Nav structure confirmed from DOM inspection:
  Trading  → Account Types | Forex Trading | Stock CFDs | MT4 | MT5
  Discover → Learning Center | Economic Calendar | Analytical Tools
  Company  → Who is XM? | Careers | Regulation

Key implementation notes:
  - All three top-level items are real <button> elements (not <a>)
  - Each has id="button_xm-www-layout" (main nav)
           or id="button_xm-www-sidebar" (mobile — excluded by filter)
  - The CDK modal-backdrop must be gone before clicking nav buttons
  - Pressing Escape + waitForFunction closes any open CDK dropdown
    before clicking the next one (prevents toggle-close on re-click)
"""

from __future__ import annotations

from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from pages.cookie_consent_page import CookieConsentPage


class NavigationPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # ── Trading sub-items ──────────────────────────────────────────
        self.account_types_link: Locator = page.get_by_role(
            "link", name="Account Types"
        )
        self.forex_trading_link: Locator = page.get_by_role(
            "link", name="Forex Trading"
        )
        self.mt4_platform_link: Locator = page.get_by_role(
            "link", name="MT4 Platform"
        )
        self.mt5_platform_link: Locator = page.get_by_role(
            "link", name="MT5 Platform"
        )

        # ── Discover sub-items ─────────────────────────────────────────
        self.learning_center_link: Locator = page.get_by_role(
            "link", name="Learning Center"
        )
        self.economic_calendar_link: Locator = page.get_by_role(
            "link", name="Economic Calendar"
        )
        self.analytical_tools_link: Locator = page.get_by_role(
            "link", name="Analytical Tools"
        )

        # ── Company sub-items ──────────────────────────────────────────
        self.about_link: Locator = page.get_by_role("link", name="Who is XM")
        self.careers_link: Locator = page.get_by_role("link", name="Careers")
        self.regulation_link: Locator = page.get_by_role("link", name="Regulation")

    # ── Shared pre-click guard ─────────────────────────────────────────

    def _prepare_for_nav_click(self) -> None:
        """
        1. Wait for cookie backdrop to be gone (it blocks pointer events)
        2. Press Escape to close any already-open CDK dropdown
        3. Wait for aria-expanded="true" to be absent (CDK closed)
        """
        consent = CookieConsentPage(self.page)
        consent.wait_for_backdrop_gone(timeout_ms=20_000)

        self.page.keyboard.press("Escape")

        # Wait for CDK to fully close any open overlay
        self.page.wait_for_function(
            "() => !document.querySelector('[aria-expanded=\"true\"]')",
            timeout=5_000,
        )
        self.page.wait_for_timeout(300)

    # ── Menu openers ───────────────────────────────────────────────────

    def open_trading_menu(self) -> None:
        self._prepare_for_nav_click()
        self.trading_menu.click()
        expect(self.account_types_link.first).to_be_visible(timeout=10_000)

    def open_discover_menu(self) -> None:
        self._prepare_for_nav_click()
        self.discover_menu.click()
        expect(self.learning_center_link.first).to_be_visible(timeout=10_000)

    def open_company_menu(self) -> None:
        self._prepare_for_nav_click()
        self.company_menu.click()
        expect(self.careers_link.first).to_be_visible(timeout=10_000)

    # ── Navigation actions ─────────────────────────────────────────────

    def go_to_account_types(self) -> None:
        self.open_trading_menu()
        link = self.account_types_link.first
        expect(link).to_be_visible(timeout=10_000)
        self.page.wait_for_timeout(500)
        # dispatch_event bypasses Angular CDK pointer-event interception
        link.dispatch_event("click")
        self.page.wait_for_url("**/account-types**", timeout=30_000)

    def go_to_economic_calendar(self) -> None:
        self.open_discover_menu()
        self.economic_calendar_link.first.click()
        self.page.wait_for_url("**/economic-calendar**", timeout=30_000)
