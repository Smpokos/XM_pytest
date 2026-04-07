"""
Homepage Tests — xm.com
Tags: @smoke, @regression
"""

import pytest
from playwright.sync_api import expect

from pages.home_page import HomePage


pytestmark = pytest.mark.smoke


class TestHomepageHero:

    def test_hero_heading_is_visible_and_contains_expected_text(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.hero_heading).to_be_visible()
        expect(home_page.hero_heading).to_contain_text("Trusted by over 20 Million")

    def test_hero_start_trading_cta_is_visible_and_clickable(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.hero_start_trading_btn).to_be_visible()
        expect(home_page.hero_start_trading_btn).to_be_enabled()

    def test_page_title_is_correct(self, home_page: HomePage) -> None:
        expect(home_page.page).to_have_title(pytest.approx("XM", rel=1))
        # More specific: title must contain XM
        assert "XM" in home_page.page.title()


class TestHomepageTickers:

    @pytest.mark.regression
    def test_key_instrument_tickers_are_displayed(
        self, home_page: HomePage
    ) -> None:
        home_page.assert_tickers_present()

    def test_eurusd_ticker_card_is_visible(self, home_page: HomePage) -> None:
        expect(home_page.eur_usd_card).to_be_visible()

    def test_gold_ticker_card_is_visible(self, home_page: HomePage) -> None:
        expect(home_page.gold_card).to_be_visible()


class TestHomepageStats:

    @pytest.mark.regression
    def test_traders_count_statistic_is_present(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.traders_count_stat).to_be_visible()

    @pytest.mark.regression
    def test_tight_spreads_feature_card_is_visible(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.tight_spreads_card).to_be_visible()

    @pytest.mark.regression
    def test_instant_withdrawals_feature_card_is_visible(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.instant_withdrawals_card).to_be_visible()


class TestHomepageNav:

    def test_login_button_is_present_in_nav(self, home_page: HomePage) -> None:
        expect(home_page.login_btn).to_be_visible()

    def test_get_started_button_is_present_in_nav(
        self, home_page: HomePage
    ) -> None:
        expect(home_page.get_started_btn).to_be_visible()


class TestHomepageFooter:

    @pytest.mark.regression
    def test_footer_privacy_policy_link_exists(
        self, home_page: HomePage
    ) -> None:
        home_page.scroll_to_footer()
        expect(home_page.footer_privacy_link).to_be_visible()

    @pytest.mark.regression
    def test_footer_cookie_policy_link_exists(
        self, home_page: HomePage
    ) -> None:
        home_page.scroll_to_footer()
        expect(home_page.footer_cookie_policy_link).to_be_visible()

    @pytest.mark.regression
    def test_footer_contains_cfd_risk_warning(
        self, home_page: HomePage
    ) -> None:
        home_page.scroll_to_footer()
        risk_warning = home_page.footer_section.get_by_text(
            "CFDs are complex instruments", exact=False
        ).first
        expect(risk_warning).to_be_visible()

    @pytest.mark.regression
    def test_footer_privacy_link_has_correct_href(
        self, home_page: HomePage
    ) -> None:
        home_page.scroll_to_footer()
        expect(home_page.footer_privacy_link).to_have_attribute(
            "href", "/privacy-policy"
        )
