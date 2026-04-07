"""
CookieConsentPage — models XM's Angular CDK cookie consent overlay.

Two confirmed flows (from live DOM inspection):
  Flow 1: "Accept All"  → single click
  Flow 2: "Modify Preferences" → opens div.cookie-modal-settings → Accept inside

Key findings from DOM debugging:
  - Buttons are real <button> elements (not <a> or <div>)
  - "Accept All" and "Modify Preferences" have no id attributes
  - The preference modal is: div[role="dialog"].modal
  - Inner wrapper is:       div.cookie-modal-settings
  - The modal-backdrop:     div.modal-backdrop (blocks nav clicks until detached)
  - XM uses server-side IP consent tracking — banner may not appear on every run
"""

from __future__ import annotations

from playwright.sync_api import Page, Locator, expect


class CookieConsentPage:
    def __init__(self, page: Page) -> None:
        self.page = page

        # ── Primary banner buttons ──────────────────────────────────────
        self.accept_all_btn: Locator = page.get_by_role(
            "button", name="Accept All", exact=True
        )
        self.modify_selection_btn: Locator = page.get_by_role(
            "button", name="Modify Preferences", exact=True
        )

        # ── Preference centre modal ─────────────────────────────────────
        # Angular CDK renders: div[role="dialog"].modal > div.cookie-modal-settings
        self.preference_centre_modal: Locator = page.locator(
            "div.cookie-modal-settings"
        )

        # Accept button inside the preference centre
        self.accept_in_preference_centre: Locator = (
            page.locator("div[role='dialog'].modal")
            .get_by_role("button", name="Accept All")
            .or_(
                page.locator("div[role='dialog'].modal")
                .get_by_role("button", name="Save")
            )
            .or_(
                page.locator("div[role='dialog'].modal")
                .get_by_role("button", name="Confirm")
            )
            .first
        )

        # Physical backdrop that blocks pointer events during animation
        self.modal_backdrop: Locator = page.locator("div.modal-backdrop")

    # ── Queries ────────────────────────────────────────────────────────

    def is_visible(self, timeout_ms: int = 8_000) -> bool:
        """Return True if the Accept All button is currently visible."""
        try:
            self.accept_all_btn.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return False

    def wait_for_banner(self, timeout_ms: int = 10_000) -> None:
        """Wait until the banner appears. Raises on timeout."""
        self.accept_all_btn.wait_for(state="visible", timeout=timeout_ms)

    # ── Flow 1: Accept All ─────────────────────────────────────────────

    def accept_all(self) -> None:
        """Click Accept All and wait for the button to disappear."""
        if self.is_visible():
            self.accept_all_btn.click()
        # Wait for button to hide — ground truth for full dismissal
        try:
            self.accept_all_btn.wait_for(state="hidden", timeout=15_000)
        except Exception:
            pass  # banner was not shown — that is fine

    # ── Flow 2: Modify → Accept ────────────────────────────────────────

    def modify_then_accept(self) -> None:
        """
        Open the preference centre then accept inside it.
        After accepting inside the modal, XM re-shows the underlying banner,
        so we call accept_all() a second time to fully dismiss.
        """
        if not self.is_visible():
            return

        self.modify_selection_btn.click()
        self.preference_centre_modal.wait_for(state="visible", timeout=8_000)
        self.accept_in_preference_centre.click()

        # Wait for preference centre to close
        try:
            self.preference_centre_modal.wait_for(state="hidden", timeout=8_000)
        except Exception:
            pass

        # XM re-shows banner after modal closes — dismiss it too
        try:
            self.accept_all_btn.wait_for(state="visible", timeout=10_000)
            self.accept_all_btn.click()
            self.modify_selection_btn.wait_for(state="hidden", timeout=15_000)
        except Exception:
            pass

    def wait_for_backdrop_gone(self, timeout_ms: int = 15_000) -> None:
        """
        Wait for the CDK modal-backdrop to disappear.
        The backdrop covers the entire page and blocks nav clicks during
        the cookie banner's CSS exit animation.
        Use 'hidden' not 'detached' — Angular CSS-hides the backdrop but
        may not remove it from DOM immediately.
        """
        try:
            self.modal_backdrop.wait_for(state="hidden", timeout=timeout_ms)
        except Exception:
            pass
