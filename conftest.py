"""
conftest.py — pytest equivalent of playwright.config.ts + fixtures/pages.ts

This file is auto-discovered by pytest. It provides:
  1. Browser launch configuration (stealth args, UA, headers)
  2. Storage-state setup (cookie consent accepted once, reused across tests)
  3. Page Object fixtures (home_page, navigation_page, etc.)

pytest-playwright hooks:
  browser_context_args — customise the BrowserContext for every test
  browser_type_launch_args — customise Chromium launch flags

Fixture scope:
  'session'  — created once for the whole run  (e.g. storage state)
  'function' — created fresh for every test    (default, e.g. page objects)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Any

import pytest
from playwright.sync_api import Page, BrowserContext, Browser, Playwright

from pages.home_page import HomePage
from pages.navigation_page import NavigationPage
from pages.cookie_consent_page import CookieConsentPage
from test_data.xm_data import STEALTH_HEADERS, REAL_USER_AGENT


# ── Auth / storage state path ──────────────────────────────────────────────
AUTH_DIR = Path(__file__).parent / "playwright" / ".auth"
CONSENT_FILE = AUTH_DIR / "consent.json"


# ── Playwright browser launch args ─────────────────────────────────────────
# These remove Chromium's automation fingerprint before any test runs.

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """
    Add stealth launch args to Chromium.

    --disable-blink-features=AutomationControlled
        Removes navigator.webdriver at the C++ level (before JS sees it).
    """
    return {
        **browser_type_launch_args,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--window-size=1440,900",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """
    Apply stealth headers and real UA to every BrowserContext.

    Why sec-ch-ua override?
      Playwright sends the real Chromium Client Hints which say
      "HeadlessChrome". Akamai reads these — not User-Agent — to detect bots.
      We override them to match a real Chrome 124 on Windows fingerprint.
    """
    return {
        **browser_context_args,
        "user_agent": REAL_USER_AGENT,
        "viewport": {"width": 1440, "height": 900},
        "extra_http_headers": STEALTH_HEADERS,
    }


# ── Session-scoped storage state (cookie consent) ─────────────────────────

@pytest.fixture(scope="session")
def accepted_consent_state(
    browser: Browser,
    browser_context_args: dict,
    browser_type_launch_args: dict,
) -> Path | None:
    """
    Navigate to xm.com once, accept cookies, and save the browser storage
    state to playwright/.auth/consent.json.

    Tests that use the 'consented_context' fixture load this file and skip
    the banner — equivalent to global-setup.ts in the TypeScript project.
    """
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(**browser_context_args)
    page = context.new_page()

    # Inject stealth before navigation
    page.add_init_script("""() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        if (!window.chrome) window.chrome = { runtime: {} };
    }""")

    try:
        page.goto("https://www.xm.com/", wait_until="commit")
        page.locator("body").wait_for(state="attached", timeout=30_000)

        consent = CookieConsentPage(page)
        consent.accept_all()
        print(f"\n[setup] Cookie consent accepted, saving state to {CONSENT_FILE}")

        context.storage_state(path=str(CONSENT_FILE))
        return CONSENT_FILE
    except Exception as e:
        print(f"\n[setup] Could not accept cookies: {e}")
        return None
    finally:
        context.close()


# ── Page fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def home_page(page: Page) -> Generator[HomePage, None, None]:
    """
    Provide a HomePage instance navigated to xm.com.

    Equivalent of the TypeScript 'homePage' fixture in fixtures/pages.ts.
    The page is already navigated and cookies dismissed before the test runs.
    """
    hp = HomePage(page)
    hp.navigate()
    yield hp


@pytest.fixture()
def navigation_page(page: Page) -> Generator[NavigationPage, None, None]:
    """Provide a NavigationPage instance navigated to xm.com."""
    np = NavigationPage(page)
    np.goto("/")
    yield np


@pytest.fixture()
def fresh_page(browser: Browser, browser_context_args: dict) -> Generator[Page, None, None]:
    """
    A fresh BrowserContext with no cookies — guarantees the consent banner
    appears. Used by cookie-consent tests that test the banner itself.
    """
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    page.add_init_script("""() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        if (!window.chrome) window.chrome = { runtime: {} };
    }""")
    page.goto("https://www.xm.com/", wait_until="commit")
    page.locator("body").wait_for(state="attached", timeout=30_000)
    yield page
    context.close()
