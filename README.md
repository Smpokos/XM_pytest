# XM.com Playwright Test Suite — Python / Pytest

A production-grade **Playwright + Python/Pytest** test suite built against [xm.com](https://www.xm.com).

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Smpokos/XM_pytest.git
cd XM_pytest

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
python -m playwright install chromium

# 5. Create the auth directory (used by session setup)
mkdir -p playwright/.auth

# 6. Run all tests headed (watch the browser)
pytest tests/ --browser chromium --headed -v

# 7. Run only smoke tests
pytest tests/ --browser chromium -m smoke -v
```

---

## Project Structure

```
XM_pytest/
│
├── .github/
│   └── workflows/
│       └── playwright.yml          # CI/CD pipeline (GitHub Actions)
│
├── pages/                          # Page Object Model
│   ├── base_page.py                # Stealth, navigation, cookie dismissal
│   ├── cookie_consent_page.py      # Accept All + Modify Preferences flows
│   ├── home_page.py                # Homepage locators and actions
│   └── navigation_page.py         # Nav dropdown interactions
│
├── tests/                          # Test specifications
│   ├── test_cookie_consent.py      # 7 tests — banner flows
│   ├── test_homepage.py            # 14 tests — content, CTAs, footer
│   ├── test_locators_showcase.py   # 12 tests — every locator strategy
│   ├── test_navigation.py          # 11 tests — dropdowns, URL routing
│   ├── test_network.py             # 5 tests  — route interception
│   └── test_websocket.py           # 5 tests  — WebSocket monitoring
│
├── utils/
│   └── websocket_monitor.py        # WS frame capture and inspection
│
├── test_data/
│   └── xm_data.py                  # Dataclasses and typed fixture data
│
├── conftest.py                     # Fixtures + browser config (= playwright.config.ts)
├── pyproject.toml                  # Project config, markers, pytest options
└── requirements.txt
```

---

## Running Tests

```bash
# All tests, verbose
pytest tests/ --browser chromium -v

# By marker
pytest tests/ --browser chromium -m smoke
pytest tests/ --browser chromium -m regression
pytest tests/ --browser chromium -m websocket
pytest tests/ --browser chromium -m cookie

# Headed (watch the browser)
pytest tests/ --browser chromium --headed -v

# Single file
pytest tests/test_homepage.py --browser chromium -v

# Single test
pytest tests/test_homepage.py::TestHomepageHero::test_hero_heading_is_visible_and_contains_expected_text --browser chromium -v

# Generate HTML report
pytest tests/ --browser chromium --html=playwright-report/report.html --self-contained-html

# Parallel execution (4 workers)
pytest tests/ --browser chromium -n 4

# Debug mode (pause on failure)
pytest tests/ --browser chromium --headed --slowmo=500 -s
```

---

## TypeScript → Python Cheat Sheet

| TypeScript (Playwright) | Python (Playwright) |
|---|---|
| `page.getByRole('button', {name:'X'})` | `page.get_by_role("button", name="X")` |
| `expect(loc).toBeVisible()` | `expect(loc).to_be_visible()` |
| `locator.first` | `locator.first` |
| `locator.filter({hasText:'X'})` | `locator.filter(has_text="X")` |
| `locatorA.or(locatorB)` | `locator_a.or_(locator_b)` |
| `page.waitForTimeout(1000)` | `page.wait_for_timeout(1_000)` |
| `page.waitForURL('**/path**')` | `page.wait_for_url("**/path**")` |
| `route.fulfill({status:200})` | `route.fulfill(status=200, body="...")` |
| `test.describe / test()` | `class TestX / def test_x()` |
| `playwright.config.ts` | `conftest.py` |
| Fixtures via `test.extend` | `@pytest.fixture` in `conftest.py` |
| `--grep @smoke` | `-m smoke` |
| `--project=chromium` | `--browser chromium` |

---

## Architecture Decisions

### conftest.py = playwright.config.ts + fixtures/pages.ts

In TypeScript, configuration and fixtures live in two separate files. Python merges both into `conftest.py`, which pytest auto-discovers:

- `browser_type_launch_args` — stealth Chromium launch flags
- `browser_context_args` — UA, viewport, sec-ch-ua headers
- `accepted_consent_state` — session-scoped: accepts cookies once, saves to `playwright/.auth/consent.json`
- `home_page`, `navigation_page` — function-scoped page object fixtures

### Anti-bot stealth layer

xm.com uses Akamai Bot Manager. Three layers defeated:

| Layer | Signal | Fix |
|---|---|---|
| HTTP | `sec-ch-ua: "HeadlessChrome"` | Override in `browser_context_args` |
| JS | `navigator.webdriver === true` | `add_init_script()` in `BasePage` |
| Chromium | `--enable-automation` flag | `--disable-blink-features=AutomationControlled` |

### Why `wait_until="commit"` not `"domcontentloaded"`

`commit` fires on the first response byte — before Akamai's JS challenge executes. `domcontentloaded` can be stalled by the challenge page. `commit` is the fastest and most reliable option for bot-protected sites.

### Cookie consent

XM's banner is a custom Angular CDK overlay — not OneTrust. Key facts:
- Buttons are real `<button>` elements with no `id` attributes
- Labels: "Accept All" and "Modify Preferences"
- Modal: `div[role="dialog"].modal` → `div.cookie-modal-settings`
- Backdrop: `div.modal-backdrop` — blocks nav clicks during animation, wait for `hidden` not `detached`

---

## Known Limitations

| Limitation | Reason | Handled |
|---|---|---|
| Nav click intermittent flakiness | CDK backdrop animation timing | `wait_for_backdrop_gone()` + Escape press |
| Banner not always shown | XM server-side IP consent tracking | Graceful skip / soft assertions |
| No WebSocket on homepage (GR) | WS only opens inside trading platform | Non-blocking conditional assertion |
| `getByLabel` test skipped | `/goto/members/en` incompatible with HTTP/2 | `@pytest.mark.skip` with explanation |

---
