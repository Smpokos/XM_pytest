"""
test_data.py — typed domain models and fixture data for xm.com tests.

Python equivalent of TypeScript interfaces + const fixture arrays.
Uses dataclasses for type safety without an ORM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal


# ── Domain types ───────────────────────────────────────────────────────────

Category = Literal["forex", "index", "commodity", "stock"]


@dataclass(frozen=True)
class Instrument:
    symbol: str       # e.g. "EURUSD"
    name: str         # e.g. "Euro vs U.S. Dollar"
    category: Category


@dataclass(frozen=True)
class NavItem:
    label: str
    href: str


@dataclass(frozen=True)
class SiteStats:
    traders_millions: float          # 20
    trades_executed_billions: float  # 11.7
    withdrawal_approval_pct: float   # 92.9


# ── Fixture data ───────────────────────────────────────────────────────────

INSTRUMENTS: List[Instrument] = [
    Instrument("EURUSD", "Euro vs U.S. Dollar", "forex"),
    Instrument("US500",  "S&P 500",             "index"),
    Instrument("GOLD",   "Gold",                "commodity"),
    Instrument("COFFEE", "US Coffee",           "commodity"),
]

EXPECTED_STATS = SiteStats(
    traders_millions=20,
    trades_executed_billions=11.7,
    withdrawal_approval_pct=92.9,
)

FOOTER_LINKS: List[NavItem] = [
    NavItem("Privacy Policy",  "/privacy-policy"),
    NavItem("Cookie Policy",   "/cookie-policy"),
]

TRADING_MENU_ITEMS: List[NavItem] = [
    NavItem("Account Types", "/account-types"),
    NavItem("Forex Trading", "/forex-trading"),
    NavItem("Stock CFDs",    "/stocks"),
    NavItem("MT4 Platform",  "/mt4"),
    NavItem("MT5 Platform",  "/mt5"),
]

# ── Stealth headers (matches playwright.config in conftest.py) ────────────

STEALTH_HEADERS = {
    "sec-ch-ua": (
        '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'
    ),
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": '"Windows"',
    "accept-language":    "en-US,en;q=0.9",
    "accept-encoding":    "gzip, deflate, br",
    "sec-fetch-dest":     "document",
    "sec-fetch-mode":     "navigate",
    "sec-fetch-site":     "none",
    "sec-fetch-user":     "?1",
    "upgrade-insecure-requests": "1",
}

REAL_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
