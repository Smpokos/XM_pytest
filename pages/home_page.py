"""
HomePage — models https://www.xm.com/

Key areas covered:
  - Hero section (h1, sub-heading, Start Trading CTA)
  - Asset ticker strip (EURUSD, US500, GOLD)
  - Statistics section
  - Feature cards (Tight Spreads, Instant Withdrawals)
  - Footer (scoped to footer.mt-auto to avoid cookie modal footer)
"""

from __future__ import annotations

from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # ── Hero ───────────────────────────────────────────────────────
        self.hero_heading: Locator = page.get_by_role("heading", level=1)
        self.hero_sub_heading: Locator = page.get_by_role("heading", level=2).first
        self.hero_start_trading_btn: Locator = (
            page.get_by_role("link", name="Start Trading").first
        )

        # ── Asset ticker strip ─────────────────────────────────────────
        # exact=True prevents strict-mode violation (symbol text also
        # appears in the description sub-text e.g. "S&P 500 (US500)")
        self.eur_usd_card: Locator = page.get_by_text("EURUSD", exact=True)
        self.us500_card: Locator = page.get_by_text("US500", exact=True)
        self.gold_card: Locator = page.get_by_text("GOLD", exact=True)

        # ── Statistics / trust section ─────────────────────────────────
        self.traders_count_stat: Locator = page.get_by_text(
            "Trusted by over 20 Million Traders", exact=False
        )

        # ── Feature cards ──────────────────────────────────────────────
        self.tight_spreads_card: Locator = page.get_by_text(
            "Tight Spreads", exact=False
        )
        self.instant_withdrawals_card: Locator = page.get_by_text(
            "Instant Withdrawals", exact=False
        )

        # ── Footer ─────────────────────────────────────────────────────
        # Scope to footer.mt-auto (page-level footer).
        # The cookie modal also has a <footer class="modal-footer"> — both
        # would match get_by_role('contentinfo'), causing a strict-mode
        # violation. The class-based selector is unique to the page footer.
        self.footer_section: Locator = page.locator("footer.mt-auto")
        self.footer_privacy_link: Locator = self.footer_section.get_by_role(
            "link", name="Privacy Policy"
        )
        self.footer_cookie_policy_link: Locator = self.footer_section.get_by_role(
            "link", name="Cookie Policy"
        )

    def navigate(self) -> None:
        """Navigate to the homepage."""
        self.goto("/")

    def assert_hero_visible(self) -> None:
        expect(self.hero_heading).to_be_visible()
        expect(self.hero_start_trading_btn).to_be_visible()

    def assert_tickers_present(self) -> None:
        expect(self.eur_usd_card).to_be_visible()
        expect(self.us500_card).to_be_visible()
        expect(self.gold_card).to_be_visible()

    def scroll_to_footer(self) -> None:
        self.footer_section.scroll_into_view_if_needed()
