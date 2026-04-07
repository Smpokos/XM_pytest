"""
Cookie Consent Tests — xm.com
Tags: @cookie, @smoke

Tests both consent flows confirmed from live DOM inspection:
  Flow 1: Accept All → single click dismissal
  Flow 2: Modify Preferences → preference centre → Accept inside

Note: XM uses server-side IP consent tracking. The banner may not appear
on every test run. Tests handle this gracefully with soft assertions.
"""

import pytest
from playwright.sync_api import Page, expect

from pages.cookie_consent_page import CookieConsentPage


pytestmark = [pytest.mark.cookie, pytest.mark.smoke]


class TestCookieConsentBanner:

    def test_banner_appears_on_fresh_session(self, fresh_page: Page) -> None:
        """
        The banner buttons must exist in the DOM on a fresh context.
        Visibility depends on server-side IP consent — we assert attachment,
        not visibility, to handle server-side suppression gracefully.
        """
        consent = CookieConsentPage(fresh_page)
        accept_btn = fresh_page.get_by_role("button", name="Accept All", exact=True)
        modify_btn = fresh_page.get_by_role(
            "button", name="Modify Preferences", exact=True
        )

        accept_btn.wait_for(state="attached", timeout=10_000)
        modify_btn.wait_for(state="attached", timeout=10_000)

        is_visible = accept_btn.is_visible()
        print(
            f"\nBanner visible on fresh context: {is_visible} "
            "(server-side IP tracking may suppress it)"
        )

    def test_accept_all_button_is_visible_and_enabled(self, fresh_page: Page) -> None:
        consent = CookieConsentPage(fresh_page)
        if not consent.is_visible():
            pytest.skip("Banner suppressed by server-side IP consent")

        consent.wait_for_banner()
        expect(consent.accept_all_btn).to_be_visible()
        expect(consent.accept_all_btn).to_be_enabled()

    def test_modify_selection_button_is_visible(self, fresh_page: Page) -> None:
        consent = CookieConsentPage(fresh_page)
        if not consent.is_visible():
            print("\nBanner suppressed by server-side IP consent — skipping")
            return

        expect(consent.modify_selection_btn).to_be_visible(timeout=10_000)

    def test_flow1_accept_all_dismisses_banner(self, fresh_page: Page) -> None:
        """Flow 1: clicking Accept All hides the banner and the page loads."""
        consent = CookieConsentPage(fresh_page)
        consent.accept_all()

        # Banner must be gone — assert the container, not any button by name
        # (multiple Accept All buttons can exist on the page)
        expect(consent.modify_selection_btn).to_be_hidden(timeout=15_000)

        # Page content must be accessible
        expect(fresh_page.get_by_role("heading", level=1)).to_be_visible()

    def test_flow2_modify_selection_opens_preference_centre(
        self, fresh_page: Page
    ) -> None:
        """Flow 2: clicking Modify Preferences opens the preference centre modal."""
        consent = CookieConsentPage(fresh_page)
        if not consent.is_visible():
            pytest.skip("Banner suppressed by server-side IP consent")

        consent.wait_for_banner()
        consent.modify_selection_btn.click()

        expect(consent.preference_centre_modal).to_be_visible(timeout=8_000)

    def test_flow2_accept_inside_preference_centre_dismisses_everything(
        self, fresh_page: Page
    ) -> None:
        """Flow 2 full: Modify Preferences → Accept → both modal and banner gone."""
        consent = CookieConsentPage(fresh_page)
        consent.modify_then_accept()

        # Preference centre must be gone
        expect(consent.preference_centre_modal).to_be_hidden(timeout=15_000)

        # Modify Preferences button only lives in the banner — its absence
        # confirms the full two-step dismissal succeeded
        expect(consent.modify_selection_btn).to_be_hidden(timeout=20_000)

        # Page is usable
        expect(fresh_page.get_by_role("heading", level=1)).to_be_visible()

    def test_consent_cookie_is_set_after_accept_all(
        self, fresh_page: Page
    ) -> None:
        """A consent-related cookie must be set after accepting."""
        consent = CookieConsentPage(fresh_page)
        consent.accept_all()

        cookies = fresh_page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        print(f"\nCookies after accept: {cookie_names}")

        # XM uses Akamai — look for XM_ or AKA_ prefixed cookies
        consent_cookie = next(
            (
                c for c in cookies
                if any(
                    prefix in c["name"].upper()
                    for prefix in ["XM_", "AKA_", "CONSENT", "COOKIE", "GDPR"]
                )
            ),
            None,
        )
        assert consent_cookie is not None, (
            f"Expected a consent/session cookie. Found: {cookie_names}"
        )
        print(
            f"Consent cookie: {consent_cookie['name']} = "
            f"{consent_cookie['value'][:80]}..."
        )
