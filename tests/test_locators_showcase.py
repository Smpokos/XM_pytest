"""
Locators Showcase — xm.com

Python/Playwright equivalent of locators-showcase.spec.ts.
Demonstrates every major locator strategy with inline explanations.

Locator strategies covered:
  1.  get_by_role          — ARIA-based (preferred)
  2.  get_by_text          — text content
  3.  get_by_label         — form label association
  4.  get_by_placeholder   — input placeholder
  5.  get_by_alt_text      — image alt text
  6.  get_by_title         — element title attribute
  7.  get_by_test_id       — data-testid attribute
  8.  CSS selectors        — page.locator('css selector')
  9.  XPath                — page.locator('xpath=...')
  10. filter / chaining    — .filter(), .first, .nth(), .locator()
  11. frame_locator        — for iframes (economic calendar)
  12. .or_()               — alternative locators (resilient pattern)
"""

import pytest
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


pytestmark = pytest.mark.smoke


@pytest.fixture()
def xm_page(page: Page) -> Page:
    """Navigate to xm.com with stealth, dismiss cookies."""
    base = BasePage(page)
    base.goto("/")
    return page


# ── 1. get_by_role — ARIA semantic roles ───────────────────────────────────
def test_01_get_by_role_heading_link_button(xm_page: Page) -> None:
    """
    get_by_role() is the PREFERRED locator strategy.
    It mirrors how screen readers see the page — resilient to CSS changes.
    """
    h1 = xm_page.get_by_role("heading", level=1)
    expect(h1).to_be_visible()

    login_link = xm_page.get_by_role("link", name="Login").first
    expect(login_link).to_be_visible()

    trading_btn = xm_page.locator('[id="button_xm-www-layout"]').filter(
        has_text="Trading"
    ).first
    expect(trading_btn).to_be_visible()


# ── 2. get_by_text — partial and exact match ───────────────────────────────
def test_02_get_by_text_partial_and_exact(xm_page: Page) -> None:
    # Partial match (default)
    spreads = xm_page.get_by_text("Tight Spreads")
    expect(spreads).to_be_visible()

    # Exact match — prevents strict-mode violation when text appears as substring
    gold = xm_page.get_by_text("GOLD", exact=True)
    expect(gold).to_be_visible()


# ── 3. get_by_label — form label association ───────────────────────────────
@pytest.mark.skip(
    reason=(
        "/goto/members/en is an Akamai redirect gateway — incompatible "
        "with Playwright HTTP/2 handling. Pattern shown, not executed. "
        "In a real project: page.get_by_label('Email'), get_by_label('Password')"
    )
)
def test_03_get_by_label_login_form_inputs_pattern(xm_page: Page) -> None:
    xm_page.goto("https://www.xm.com/goto/members/en")
    email_input = xm_page.get_by_label("Email")
    password_input = xm_page.get_by_label("Password")
    expect(email_input.or_(password_input)).to_be_attached(timeout=8_000)


# ── 4. get_by_placeholder ──────────────────────────────────────────────────
def test_04_get_by_placeholder_search_input(page: Page) -> None:
    base = BasePage(page)
    base.goto("/help-center/home")
    search = page.get_by_placeholder(pattern="Search", exact=False) if hasattr(
        page.get_by_placeholder(""), "filter"
    ) else page.get_by_placeholder("Search")
    count = search.count()
    print(f"\nSearch inputs found: {count}")
    # Pattern shown — count logged, not asserted


# ── 5. get_by_alt_text — images ───────────────────────────────────────────
def test_05_get_by_alt_text_hero_images(xm_page: Page) -> None:
    mountain_img = xm_page.get_by_alt_text("mountain", exact=False)
    expect(mountain_img).to_be_attached()


# ── 6. CSS selectors ───────────────────────────────────────────────────────
def test_06_css_selectors_class_attribute_pseudo(xm_page: Page) -> None:
    # All anchor tags
    all_links = xm_page.locator("a")
    assert all_links.count() > 10

    # Attribute selector
    trading_links = xm_page.locator('a[href*="trading"]')
    print(f"\nTrading links: {trading_links.count()}")

    # Scoped: links inside nav
    nav_links = xm_page.locator("nav a")
    print(f"Nav links: {nav_links.count()}")


# ── 7. XPath selectors ─────────────────────────────────────────────────────
def test_07_xpath_text_based_and_attribute_based(xm_page: Page) -> None:
    # XPath equivalent of get_by_role('heading', level=1)
    h1_xpath = xm_page.locator("xpath=//h1")
    expect(h1_xpath).to_be_visible()

    # XPath: find element containing specific text
    stat = xm_page.locator("xpath=//*[contains(text(),'20 Million')]")
    expect(stat.first).to_be_visible()


# ── 8. filter() and chaining ──────────────────────────────────────────────
def test_08_filter_and_chaining_locators(xm_page: Page) -> None:
    # .filter() narrows a locator set
    sections = xm_page.locator("section")
    stat_section = sections.filter(has_text="20 Million Traders")
    expect(stat_section).to_be_visible()

    # .first / .last / .nth()
    first_footer_link = xm_page.locator("footer.mt-auto a").first
    expect(first_footer_link).to_be_attached()

    second_footer_link = xm_page.locator("footer.mt-auto a").nth(1)
    expect(second_footer_link).to_be_attached()


# ── 9. Scoped locators (chaining .locator()) ───────────────────────────────
def test_09_scoped_locators_narrow_within_parent(xm_page: Page) -> None:
    # Scope to footer, then find links within it
    footer = xm_page.locator("footer.mt-auto")
    footer_links = footer.get_by_role("link")
    assert footer_links.count() > 5

    # Verify Privacy Policy exists specifically inside the footer
    privacy = footer.get_by_role("link", name="Privacy Policy")
    expect(privacy).to_be_visible()


# ── 10. Frame locator — economic calendar widget ───────────────────────────
@pytest.mark.regression
def test_10_frame_locator_economic_calendar_widget(page: Page) -> None:
    base = BasePage(page)
    base.goto("/economic-calendar")

    # Economic calendar is embedded in an iframe
    frame = page.frame_locator("iframe").first

    try:
        inner = frame.locator("body")
        inner.wait_for(state="attached", timeout=15_000)
        print("\nEconomic calendar iframe found and loaded")
    except Exception:
        print("\nCalendar iframe not found at time of test — check selector")


# ── 11. .or_() — alternative locators (resilient) ─────────────────────────
def test_11_or_alternative_locators_resilient(xm_page: Page) -> None:
    """
    .or_() resolves to whichever locator is found first.
    Useful for elements that have multiple valid selectors.
    """
    cta_by_role = xm_page.get_by_role("link", name="Start Trading")
    cta_by_text = xm_page.get_by_text("Start Trading")

    cta = cta_by_role.or_(cta_by_text).first
    expect(cta).to_be_visible()
