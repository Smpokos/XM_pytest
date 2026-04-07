"""
Navigation Tests — xm.com main nav dropdowns and URL routing.
Tags: @smoke, @regression
"""

import pytest
from playwright.sync_api import Page, expect

from pages.navigation_page import NavigationPage


pytestmark = pytest.mark.smoke


class TestTradingMenu:

    def test_trading_menu_opens_and_reveals_account_types_link(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_trading_menu()
        expect(navigation_page.account_types_link.first).to_be_visible()

    def test_trading_menu_reveals_mt4_and_mt5_platform_links(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_trading_menu()
        expect(navigation_page.mt4_platform_link.first).to_be_visible()
        expect(navigation_page.mt5_platform_link.first).to_be_visible()

    @pytest.mark.regression
    def test_clicking_account_types_navigates_to_account_types(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.go_to_account_types()
        expect(navigation_page.page).to_have_url(
            pattern=".*account-types.*", timeout=30_000
        )


class TestDiscoverMenu:

    def test_discover_menu_opens_and_shows_learning_center_link(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_discover_menu()
        expect(navigation_page.learning_center_link.first).to_be_visible()

    def test_discover_menu_shows_economic_calendar_link(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_discover_menu()
        expect(navigation_page.economic_calendar_link.first).to_be_visible()

    @pytest.mark.regression
    def test_clicking_economic_calendar_navigates_correctly(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.go_to_economic_calendar()
        expect(navigation_page.page).to_have_url(
            pattern=".*economic-calendar.*", timeout=30_000
        )


class TestCompanyMenu:

    def test_company_menu_opens_and_shows_careers_link(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_company_menu()
        expect(navigation_page.careers_link.first).to_be_visible()

    def test_company_menu_shows_regulation_link(
        self, navigation_page: NavigationPage
    ) -> None:
        navigation_page.open_company_menu()
        expect(navigation_page.regulation_link.first).to_be_visible()


class TestDirectNavigation:
    """Direct URL navigation — no dropdown interaction needed."""

    @pytest.mark.regression
    def test_direct_navigation_to_forex_trading_returns_200(
        self, page: Page
    ) -> None:
        response = page.goto("https://www.xm.com/forex-trading")
        assert response is not None
        assert response.status == 200

    @pytest.mark.regression
    def test_direct_navigation_to_mt4_returns_200(self, page: Page) -> None:
        response = page.goto("https://www.xm.com/mt4")
        assert response is not None
        assert response.status == 200

    @pytest.mark.regression
    def test_direct_navigation_to_about_returns_200(self, page: Page) -> None:
        response = page.goto("https://www.xm.com/about")
        assert response is not None
        assert response.status == 200
