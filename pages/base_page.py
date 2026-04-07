"""
BasePage — all Page Objects inherit from this.

Responsibilities:
  1. Inject stealth init script (mask navigator.webdriver)
  2. Navigate with waitUntil='commit' (escapes Akamai bot-detection stall)
  3. Dismiss cookie consent via CookieConsentPage
  4. Expose shared nav locators

Python/Playwright notes:
  - page.locator()  returns a Locator (same concept as TypeScript)
  - expect(locator) is playwright.sync_api.expect (auto-retrying assertions)
  - All Playwright calls are synchronous in pytest-playwright by default
"""

from __future__ import annotations

from playwright.sync_api import Page, Locator


STEALTH_SCRIPT = """
() => {
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    const uaData = {
        brands: [
            { brand: 'Chromium',      version: '124' },
            { brand: 'Google Chrome', version: '124' },
            { brand: 'Not-A.Brand',   version: '99'  },
        ],
        mobile: false,
        platform: 'Windows',
        getHighEntropyValues: async () => ({
            architecture: 'x86', bitness: '64', mobile: false,
            platform: 'Windows', platformVersion: '10.0.0',
            uaFullVersion: '124.0.0.0',
        }),
    };
    Object.defineProperty(navigator, 'userAgentData', {
        get: () => uaData,
        configurable: true
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => Object.assign([], { length: 3 })
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    if (!window.chrome) {
        window.chrome = { runtime: {}, loadTimes: () => ({}), csi: () => ({}) };
    }
}
"""


class BasePage:
    BASE_URL = "https://www.xm.com"

    def __init__(self, page: Page) -> None:
        self.page = page

        # ── Cookie / consent banner ────────────────────────────────────
        self.cookie_accept_btn: Locator = page.get_by_role(
            "button", name="Accept All", exact=True
        )
        self.cookie_reject_btn: Locator = page.get_by_role(
            "button", name="Reject", exact=True
        )

        # ── Global nav ─────────────────────────────────────────────────
        # id="button_xm-www-layout" = main nav buttons
        # id="button_xm-www-sidebar" = mobile sidebar (excluded by filter)
        self.login_btn: Locator = page.get_by_role("link", name="Login").first
        self.get_started_btn: Locator = (
            page.get_by_role("link", name="Get Started").first
        )
        self.trading_menu: Locator = (
            page.locator('[id="button_xm-www-layout"]')
            .filter(has_text="Trading")
            .first
        )
        self.discover_menu: Locator = (
            page.locator('[id="button_xm-www-layout"]')
            .filter(has_text="Discover")
            .first
        )
        self.company_menu: Locator = (
            page.locator('[id="button_xm-www-layout"]')
            .filter(has_text="Company")
            .first
        )

    # ── Stealth ────────────────────────────────────────────────────────

    def inject_stealth_script(self) -> None:
        """
        Mask navigator.webdriver and spoof userAgentData BEFORE page load.
        add_init_script schedules the script to run in every new document
        context, before any page JS executes.
        """
        self.page.add_init_script(STEALTH_SCRIPT)

    # ── Navigation ─────────────────────────────────────────────────────

    def goto(self, path: str = "/") -> None:
        """
        Navigate to a path on xm.com.

        waitUntil='commit'
            Fires on first response byte — before Akamai's JS challenge
            can execute. We then wait for body to confirm a real page loaded.
        """
        self.inject_stealth_script()
        url = self.BASE_URL + path if path.startswith("/") else path
        self.page.goto(url, wait_until="commit")
        self.page.locator("body").wait_for(state="attached", timeout=30_000)
        self.dismiss_cookies()

    def dismiss_cookies(self) -> None:
        """Accept the cookie banner if it appears (best-effort, non-blocking)."""
        from pages.cookie_consent_page import CookieConsentPage

        consent = CookieConsentPage(self.page)
        consent.accept_all()

    def wait_for_page_load(self) -> None:
        """Wait for DOM to be interactive (prefer over networkidle — XM has persistent WS)."""
        self.page.wait_for_load_state("domcontentloaded")
