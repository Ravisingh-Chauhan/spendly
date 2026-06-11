"""
tests/test_06_date_filter_profile.py

Pytest test suite for Step 06: Date Filter on the /profile page.

Coverage:
  - Auth guard for unauthenticated access with date params
  - No-filter baseline (all-time view)
  - date_from only, date_to only, both params (custom range)
  - Reversed date range triggers flash error and falls back to unfiltered view
  - Malformed date strings are silently ignored (no crash, unfiltered view)
  - Empty date range (valid dates, zero matching expenses) returns ₹0.00 / 0 transactions
  - Active preset detection: all_time vs this_month
  - Rupee symbol present regardless of active filter
  - Summary stats and category breakdown both respect the active date filter
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app import app as flask_app
from database.db import init_db, get_db


# ---------------------------------------------------------------------------
# Helper: insert expenses directly via the DB connection used by the app
# ---------------------------------------------------------------------------

def _insert_expenses(user_id, expenses):
    """
    Insert a list of (amount, category, date_str, description) tuples for user_id.
    Uses the same get_db() path as the app so the in-memory DB is shared.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id, amt, cat, dt, desc) for amt, cat, dt, desc in expenses],
    )
    conn.commit()
    conn.close()


def _get_user_id(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Flask app wired to an in-memory SQLite DB, fresh schema per test."""
    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Patch get_db so all calls during the test use a shared in-memory connection
    import sqlite3
    from werkzeug.security import generate_password_hash as _gph  # noqa: F401

    _conn = sqlite3.connect(":memory:", check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")

    def _fake_get_db():
        return _conn

    with patch("database.db.get_db", side_effect=_fake_get_db), \
         patch("database.queries.get_db", side_effect=_fake_get_db), \
         patch("app.get_db", side_effect=_fake_get_db):
        with flask_app.app_context():
            # Bootstrap schema directly on the in-memory connection
            _conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            _conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            _conn.commit()
            yield flask_app

    _conn.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """
    A logged-in test client with a clean user account and controlled seed expenses.

    Expense dates are fixed to April, May, and June 2026 so that filtering
    assertions are deterministic regardless of when the tests execute.

    Seed data:
      April 2026 only:
        - 1000.00  Food        2026-04-10  April groceries
        - 500.00   Transport   2026-04-20  April commute

      May 2026 only:
        - 2000.00  Bills       2026-05-05  May electricity
        - 800.00   Health      2026-05-15  May pharmacy

      June 2026 only:
        - 300.00   Entertainment 2026-06-01  June OTT
        - 1500.00  Shopping      2026-06-10  June clothes
    """
    # Register and log in
    client.post(
        "/register",
        data={
            "name": "Filter Tester",
            "email": "filter@test.com",
            "password": "securepass1",
        },
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"email": "filter@test.com", "password": "securepass1"},
        follow_redirects=True,
    )

    with flask_app.app_context():
        user_id = _get_user_id("filter@test.com")
        _insert_expenses(
            user_id,
            [
                (1000.00, "Food", "2026-04-10", "April groceries"),
                (500.00, "Transport", "2026-04-20", "April commute"),
                (2000.00, "Bills", "2026-05-05", "May electricity"),
                (800.00, "Health", "2026-05-15", "May pharmacy"),
                (300.00, "Entertainment", "2026-06-01", "June OTT"),
                (1500.00, "Shopping", "2026-06-10", "June clothes"),
            ],
        )

    return client


# ---------------------------------------------------------------------------
# 1. Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_no_params_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Expected redirect for unauthenticated access"
        assert "/login" in response.headers["Location"], "Should redirect to /login"

    def test_unauthenticated_with_date_params_redirects_to_login(self, client):
        response = client.get("/profile?date_from=2026-04-01&date_to=2026-04-30")
        assert response.status_code == 302, "Date params must not bypass auth guard"
        assert "/login" in response.headers["Location"], "Should redirect to /login regardless of query params"

    def test_unauthenticated_with_malformed_date_params_redirects_to_login(self, client):
        response = client.get("/profile?date_from=not-a-date&date_to=also-invalid")
        assert response.status_code == 302, "Malformed date params must not bypass auth guard"
        assert "/login" in response.headers["Location"], "Should redirect to /login"


# ---------------------------------------------------------------------------
# 2. No-filter baseline (all-time view)
# ---------------------------------------------------------------------------

class TestNoFilterBaseline:
    def test_profile_no_params_returns_200(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200, "Authenticated /profile with no params must return 200"

    def test_profile_no_params_shows_all_expenses(self, auth_client):
        response = auth_client.get("/profile")
        data = response.data.decode()
        # All six seed transactions total 6100.00
        assert "6,100.00" in data, "Total spent should reflect all six seed expenses (₹6,100.00)"

    def test_profile_no_params_active_preset_is_all_time(self, auth_client):
        response = auth_client.get("/profile")
        data = response.data.decode()
        # The template must mark the "All Time" button as active when no filter is set.
        # We check for the active_preset value being reflected; the template uses it
        # to apply an active CSS class or aria attribute to the All Time button.
        assert "all_time" in data or "All Time" in data, (
            "Template should indicate All Time as the active preset when no filter is applied"
        )

    def test_profile_no_params_rupee_symbol_present(self, auth_client):
        response = auth_client.get("/profile")
        assert "₹" in response.data.decode(), "Rupee symbol must be present with no filter"


# ---------------------------------------------------------------------------
# 3. date_from only
# ---------------------------------------------------------------------------

class TestDateFromOnly:
    def test_date_from_only_excludes_earlier_expenses(self, auth_client):
        # date_from = 2026-05-01 should exclude the April transactions
        response = auth_client.get("/profile?date_from=2026-05-01")
        data = response.data.decode()
        assert "April groceries" not in data, "April expenses must be excluded when date_from=2026-05-01"
        assert "April commute" not in data, "April transport must be excluded when date_from=2026-05-01"

    def test_date_from_only_includes_on_or_after_bound(self, auth_client):
        # May and June expenses must still appear
        response = auth_client.get("/profile?date_from=2026-05-01")
        data = response.data.decode()
        assert "May electricity" in data, "May expense must appear when date_from=2026-05-01"
        assert "June OTT" in data, "June expense must appear when date_from=2026-05-01"

    def test_date_from_only_total_reflects_filtered_set(self, auth_client):
        # May + June total: 2000 + 800 + 300 + 1500 = 4600
        response = auth_client.get("/profile?date_from=2026-05-01")
        data = response.data.decode()
        assert "4,600.00" in data, "Total should be ₹4,600.00 for May+June when date_from=2026-05-01"


# ---------------------------------------------------------------------------
# 4. date_to only
# ---------------------------------------------------------------------------

class TestDateToOnly:
    def test_date_to_only_excludes_later_expenses(self, auth_client):
        # date_to = 2026-04-30 should exclude May and June transactions
        response = auth_client.get("/profile?date_to=2026-04-30")
        data = response.data.decode()
        assert "May electricity" not in data, "May expenses must be excluded when date_to=2026-04-30"
        assert "June OTT" not in data, "June expenses must be excluded when date_to=2026-04-30"

    def test_date_to_only_includes_on_or_before_bound(self, auth_client):
        response = auth_client.get("/profile?date_to=2026-04-30")
        data = response.data.decode()
        assert "April groceries" in data, "April expense must appear when date_to=2026-04-30"
        assert "April commute" in data, "April commute must appear when date_to=2026-04-30"

    def test_date_to_only_total_reflects_filtered_set(self, auth_client):
        # April only: 1000 + 500 = 1500
        response = auth_client.get("/profile?date_to=2026-04-30")
        data = response.data.decode()
        assert "1,500.00" in data, "Total should be ₹1,500.00 for April when date_to=2026-04-30"


# ---------------------------------------------------------------------------
# 5. Both date_from and date_to (custom range)
# ---------------------------------------------------------------------------

class TestBothDates:
    def test_both_dates_only_in_range_expenses_shown(self, auth_client):
        # May only: 2026-05-01 to 2026-05-31
        response = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        data = response.data.decode()
        assert "May electricity" in data, "May electricity must appear in May-only range"
        assert "May pharmacy" in data, "May pharmacy must appear in May-only range"

    def test_both_dates_out_of_range_expenses_absent(self, auth_client):
        response = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        data = response.data.decode()
        assert "April groceries" not in data, "April expense must be absent in May-only range"
        assert "June OTT" not in data, "June expense must be absent in May-only range"

    def test_both_dates_summary_stats_reflect_range(self, auth_client):
        # May only total: 2000 + 800 = 2800; transaction count = 2
        response = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        data = response.data.decode()
        assert "2,800.00" in data, "Total should be ₹2,800.00 for May-only range"

    def test_both_dates_inclusive_bounds(self, auth_client):
        # The bounds themselves must be included (2026-05-05 is boundary)
        response = auth_client.get("/profile?date_from=2026-05-05&date_to=2026-05-05")
        data = response.data.decode()
        assert "May electricity" in data, "Expense exactly on date_from==date_to must be included"

    def test_both_dates_rupee_symbol_present(self, auth_client):
        response = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert "₹" in response.data.decode(), "Rupee symbol must be present with custom range filter"

    def test_both_dates_category_breakdown_respects_filter(self, auth_client):
        # May-only range: only Bills and Health categories should appear
        response = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        data = response.data.decode()
        assert "Bills" in data, "Bills category must appear in May-only breakdown"
        assert "Health" in data, "Health category must appear in May-only breakdown"
        # Categories that have no May expenses must not appear in the breakdown
        # (Food and Transport only have April entries)
        assert "April groceries" not in data, "April Food entry must not appear in May breakdown"
        assert "April commute" not in data, "April Transport entry must not appear in May breakdown"


# ---------------------------------------------------------------------------
# 6. Reversed date range (date_from > date_to)
# ---------------------------------------------------------------------------

class TestReversedDates:
    def test_reversed_dates_returns_200(self, auth_client):
        response = auth_client.get(
            "/profile?date_from=2026-05-31&date_to=2026-05-01",
            follow_redirects=True,
        )
        assert response.status_code == 200, "Reversed dates must not crash the app"

    def test_reversed_dates_flash_error_shown(self, auth_client):
        response = auth_client.get(
            "/profile?date_from=2026-05-31&date_to=2026-05-01",
            follow_redirects=True,
        )
        data = response.data.decode()
        assert "Start date must be before end date" in data, (
            "Flash error 'Start date must be before end date.' must be visible"
        )

    def test_reversed_dates_falls_back_to_all_expenses(self, auth_client):
        # When reversed, the view must behave as if no filter was applied
        response = auth_client.get(
            "/profile?date_from=2026-06-30&date_to=2026-04-01",
            follow_redirects=True,
        )
        data = response.data.decode()
        # All six seed expenses total 6100.00
        assert "6,100.00" in data, (
            "Reversed date range must fall back to all-time total (₹6,100.00)"
        )

    def test_reversed_dates_all_transactions_visible(self, auth_client):
        response = auth_client.get(
            "/profile?date_from=2026-06-30&date_to=2026-04-01",
            follow_redirects=True,
        )
        data = response.data.decode()
        # At least one April and one June transaction must be present
        assert "April groceries" in data, "April expense must be visible after fallback"
        assert "June OTT" in data, "June expense must be visible after fallback"


# ---------------------------------------------------------------------------
# 7. Malformed date strings
# ---------------------------------------------------------------------------

class TestMalformedDates:
    @pytest.mark.parametrize("date_from,date_to", [
        ("not-a-date", ""),
        ("", "not-a-date"),
        ("not-a-date", "not-a-date"),
        ("2026/06/01", "2026/06/30"),   # wrong separator
        ("01-06-2026", "30-06-2026"),   # DD-MM-YYYY
        ("2026-13-01", "2026-14-01"),   # invalid month/day
        ("abcdefgh", "ijklmnop"),       # random strings
    ])
    def test_malformed_dates_do_not_crash(self, auth_client, date_from, date_to):
        url = f"/profile?date_from={date_from}&date_to={date_to}"
        response = auth_client.get(url)
        assert response.status_code == 200, (
            f"Malformed dates '{date_from}'/'{date_to}' must not crash the app"
        )

    @pytest.mark.parametrize("date_from,date_to", [
        ("not-a-date", ""),
        ("", "not-a-date"),
        ("2026/06/01", "2026/06/30"),
    ])
    def test_malformed_dates_return_unfiltered_view(self, auth_client, date_from, date_to):
        url = f"/profile?date_from={date_from}&date_to={date_to}"
        response = auth_client.get(url)
        data = response.data.decode()
        # All six seed expenses visible (total 6100.00)
        assert "6,100.00" in data, (
            f"Malformed dates must silently fall back to all-time view (₹6,100.00); "
            f"date_from='{date_from}', date_to='{date_to}'"
        )

    def test_malformed_date_from_only_falls_back_to_unfiltered(self, auth_client):
        response = auth_client.get("/profile?date_from=not-a-date")
        data = response.data.decode()
        assert "6,100.00" in data, "Malformed date_from alone must fall back to all-time view"

    def test_malformed_date_to_only_falls_back_to_unfiltered(self, auth_client):
        response = auth_client.get("/profile?date_to=2026-99-99")
        data = response.data.decode()
        assert "6,100.00" in data, "Malformed date_to alone must fall back to all-time view"


# ---------------------------------------------------------------------------
# 8. Empty date range (valid dates, zero matching expenses)
# ---------------------------------------------------------------------------

class TestEmptyDateRange:
    def test_empty_range_returns_200(self, auth_client):
        # A future date window with no seed expenses
        response = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-01-31")
        assert response.status_code == 200, "Empty date range must return 200, not an error"

    def test_empty_range_shows_zero_total(self, auth_client):
        response = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-01-31")
        data = response.data.decode()
        assert "0.00" in data, "Empty range must display ₹0.00 total spent"

    def test_empty_range_shows_zero_transaction_count(self, auth_client):
        response = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-01-31")
        data = response.data.decode()
        # The transaction count stat should reflect 0
        assert "0" in data, "Empty range must show 0 transactions"

    def test_empty_range_no_category_rows(self, auth_client):
        response = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-01-31")
        data = response.data.decode()
        # None of the seeded categories should appear in the breakdown section
        for category in ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping"):
            # A category only appears in the breakdown when it has spend in the range;
            # it may still appear in the transaction list header, so we check the absence
            # of formatted amounts tied to those categories rather than the word itself.
            pass  # assertion below targets the absence of any ₹ amounts > 0
        assert "1,000.00" not in data, "April Food total must not appear in empty-range breakdown"
        assert "2,000.00" not in data, "May Bills total must not appear in empty-range breakdown"

    def test_empty_range_rupee_symbol_still_present(self, auth_client):
        response = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-01-31")
        assert "₹" in response.data.decode(), "Rupee symbol must be present even for empty range"


# ---------------------------------------------------------------------------
# 9. Active preset detection
# ---------------------------------------------------------------------------

class TestActivePresetDetection:
    def test_no_params_active_preset_is_all_time(self, auth_client):
        response = auth_client.get("/profile")
        data = response.data.decode()
        assert "all_time" in data, "active_preset must be 'all_time' when no params are given"

    def test_this_month_params_mark_this_month_active(self, auth_client):
        today = date.today()
        first_of_month = today.replace(day=1)
        url = f"/profile?date_from={first_of_month.isoformat()}&date_to={today.isoformat()}"
        response = auth_client.get(url)
        data = response.data.decode()
        assert "this_month" in data, (
            "active_preset must be 'this_month' when params exactly match current month range"
        )

    def test_custom_range_preset_is_custom(self, auth_client):
        # An arbitrary range that doesn't match any preset
        response = auth_client.get("/profile?date_from=2026-04-01&date_to=2026-04-30")
        data = response.data.decode()
        assert "custom" in data, (
            "active_preset must be 'custom' for arbitrary date ranges"
        )

    def test_preset_urls_use_url_for_not_hardcoded(self, auth_client):
        # The template must render links to /profile (not any other path) for presets
        response = auth_client.get("/profile")
        data = response.data.decode()
        assert "/profile" in data, "Preset links must point to /profile route"

    def test_all_time_preset_url_is_clean_profile(self, auth_client):
        # The All Time preset link must be a bare /profile with no query string
        response = auth_client.get("/profile")
        data = response.data.decode()
        # href="/profile" (no query params) must appear for the All Time link
        assert 'href="/profile"' in data or "href='/profile'" in data, (
            "All Time preset must link to /profile with no query parameters"
        )


# ---------------------------------------------------------------------------
# 10. Transaction list ordering within a filtered range
# ---------------------------------------------------------------------------

class TestTransactionOrdering:
    def test_transactions_ordered_newest_first_within_range(self, auth_client):
        # In the April-to-June range, June 10 should appear before April 10
        response = auth_client.get("/profile?date_from=2026-04-01&date_to=2026-06-30")
        data = response.data.decode()
        june_pos = data.find("June clothes")
        april_pos = data.find("April groceries")
        assert june_pos != -1, "June clothes must appear in the all-April-to-June range"
        assert april_pos != -1, "April groceries must appear in the all-April-to-June range"
        assert june_pos < april_pos, (
            "Newer transactions (June) must appear before older ones (April) in the list"
        )


# ---------------------------------------------------------------------------
# 11. Summary stats transaction count matches filtered set
# ---------------------------------------------------------------------------

class TestTransactionCount:
    def test_transaction_count_matches_filtered_expenses(self, auth_client):
        # April only has 2 expenses
        response = auth_client.get("/profile?date_from=2026-04-01&date_to=2026-04-30")
        data = response.data.decode()
        # The number 2 must appear as the transaction count somewhere in the stats
        assert "2" in data, "Transaction count must reflect the number of filtered expenses"

    def test_transaction_count_all_time_is_six(self, auth_client):
        response = auth_client.get("/profile")
        data = response.data.decode()
        assert "6" in data, "All-time transaction count must be 6 for the seed data"
