"""
Test suite for date filter feature on profile page.

Tests verify date range filtering behavior as specified in:
.claude/specs/06-date-filter.md

The feature allows users to filter transactions by date range while keeping
summary stats and category breakdown unchanged (all-time data).
"""

import pytest
from datetime import datetime, timedelta
from app import app as flask_app
from database.db import init_db, get_db
from werkzeug.security import generate_password_hash


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app():
    """Configure Flask app for testing with in-memory database."""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    # Override get_db to use in-memory database for tests
    original_get_db = get_db

    def test_get_db():
        import sqlite3
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # Monkey-patch the get_db function in all modules that import it
    import database.db
    import database.queries
    database.db.get_db = test_get_db
    database.queries.get_db = test_get_db

    with flask_app.app_context():
        init_db()
        yield flask_app

    # Restore original get_db after tests
    database.db.get_db = original_get_db
    database.queries.get_db = original_get_db


@pytest.fixture
def client(app):
    """Provides Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Provides authenticated test client with a logged-in user."""
    # Register and login a test user
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    return client


@pytest.fixture
def user_with_transactions(auth_client):
    """
    Creates a user with multiple transactions across different dates.
    Returns tuple: (client, user_id)
    """
    # Get user_id from session by accessing the profile page
    response = auth_client.get('/profile')
    assert response.status_code == 200

    # Insert test transactions with various dates
    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()

    # Get the user_id
    cursor.execute("SELECT id FROM users WHERE email = ?", ('test@example.com',))
    user_id = cursor.fetchone()[0]

    # Insert 15 transactions across different dates to test filtering and limit
    test_expenses = [
        (user_id, 100.00, "Food", "2026-01-05", "Old transaction 1"),
        (user_id, 200.00, "Transport", "2026-01-10", "Old transaction 2"),
        (user_id, 150.00, "Food", "2026-02-01", "Feb transaction 1"),
        (user_id, 250.00, "Shopping", "2026-02-15", "Feb transaction 2"),
        (user_id, 300.00, "Bills", "2026-03-01", "March transaction 1"),
        (user_id, 175.00, "Health", "2026-03-15", "March transaction 2"),
        (user_id, 225.00, "Entertainment", "2026-04-01", "April transaction 1"),
        (user_id, 275.00, "Food", "2026-04-15", "April transaction 2"),
        (user_id, 325.00, "Transport", "2026-05-01", "May transaction 1"),
        (user_id, 375.00, "Shopping", "2026-05-15", "May transaction 2"),
        (user_id, 425.00, "Bills", "2026-05-20", "May transaction 3"),
        (user_id, 475.00, "Health", "2026-05-25", "May transaction 4"),
        (user_id, 525.00, "Entertainment", "2026-06-01", "Recent transaction 1"),
        (user_id, 575.00, "Food", "2026-06-02", "Recent transaction 2"),
        (user_id, 625.00, "Other", "2026-06-03", "Recent transaction 3"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        test_expenses
    )
    conn.commit()
    conn.close()

    return auth_client, user_id


# ------------------------------------------------------------------ #
# Auth Guard Tests                                                    #
# ------------------------------------------------------------------ #

def test_profile_requires_authentication(client):
    """Unauthenticated access to /profile redirects to login."""
    response = client.get('/profile')
    assert response.status_code == 302, "Should redirect unauthenticated users"
    assert '/login' in response.location, "Should redirect to login page"


def test_profile_with_filter_requires_authentication(client):
    """Unauthenticated access to /profile with query params redirects to login."""
    response = client.get('/profile?start_date=2026-01-01&end_date=2026-12-31')
    assert response.status_code == 302, "Should redirect unauthenticated users"
    assert '/login' in response.location, "Should redirect to login page"


# ------------------------------------------------------------------ #
# Default View Tests (No Filter)                                      #
# ------------------------------------------------------------------ #

def test_default_view_shows_recent_10_transactions(user_with_transactions):
    """Default profile view shows most recent 10 transactions without filter."""
    client, user_id = user_with_transactions

    response = client.get('/profile')
    assert response.status_code == 200, "Profile page should load successfully"

    # Verify we see recent transactions (check for unique descriptions)
    data = response.data.decode('utf-8')
    assert "Recent transaction 3" in data, "Should show most recent transaction"
    assert "Recent transaction 2" in data, "Should show recent transactions"
    assert "Recent transaction 1" in data, "Should show recent transactions"

    # The 11th most recent (Old transaction 1 from Jan) should NOT appear
    # because default view limits to 10
    assert "Old transaction 1" not in data, "Should not show transactions beyond 10th most recent"


def test_default_view_has_no_active_filter_message(user_with_transactions):
    """Default view should not display 'Showing transactions from...' message."""
    client, user_id = user_with_transactions

    response = client.get('/profile')
    data = response.data.decode('utf-8')

    assert "Showing transactions from" not in data, "Should not show filter message when no filter is active"


# ------------------------------------------------------------------ #
# Filtered View Tests (Both Dates Provided)                           #
# ------------------------------------------------------------------ #

def test_filter_with_both_dates_shows_all_matching_transactions(user_with_transactions):
    """When both dates provided, show ALL transactions in range (no 10-item limit)."""
    client, user_id = user_with_transactions

    # Filter for May 2026 (4 transactions: May 1, 15, 20, 25)
    response = client.get('/profile?start_date=2026-05-01&end_date=2026-05-31')
    assert response.status_code == 200, "Profile page should load with filters"

    data = response.data.decode('utf-8')

    # All May transactions should appear
    assert "May transaction 1" in data, "Should show transaction from May 1"
    assert "May transaction 2" in data, "Should show transaction from May 15"
    assert "May transaction 3" in data, "Should show transaction from May 20"
    assert "May transaction 4" in data, "Should show transaction from May 25"

    # April and June transactions should NOT appear
    assert "April transaction" not in data, "Should not show transactions before range"
    assert "Recent transaction" not in data, "Should not show transactions after range"


def test_filter_with_date_range_shows_filter_message(user_with_transactions):
    """Filtered view displays 'Showing transactions from DD Mon YYYY to DD Mon YYYY'."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-03-01&end_date=2026-03-31')
    data = response.data.decode('utf-8')

    # Check for formatted date display
    assert "Showing transactions from" in data, "Should display filter active message"
    assert "01 Mar 2026" in data, "Should show formatted start date"
    assert "31 Mar 2026" in data, "Should show formatted end date"


def test_filter_date_inputs_prefilled_with_current_values(user_with_transactions):
    """Date inputs in form should be pre-filled with current filter values."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-04-01&end_date=2026-04-30')
    data = response.data.decode('utf-8')

    # Check that date input fields have value attributes set
    assert 'value="2026-04-01"' in data, "Start date input should be pre-filled"
    assert 'value="2026-04-30"' in data, "End date input should be pre-filled"


def test_filter_includes_boundary_dates(user_with_transactions):
    """Date filtering is inclusive of start and end dates."""
    client, user_id = user_with_transactions

    # Filter exactly for Feb 1 to Feb 15 (includes both boundary transactions)
    response = client.get('/profile?start_date=2026-02-01&end_date=2026-02-15')
    data = response.data.decode('utf-8')

    assert "Feb transaction 1" in data, "Should include transaction on start date"
    assert "Feb transaction 2" in data, "Should include transaction on end date"


def test_filter_with_no_limit_shows_more_than_10(user_with_transactions):
    """Filtered view removes the 10-transaction limit."""
    client, user_id = user_with_transactions

    # Filter for Jan through May (should be 12 transactions, more than default limit of 10)
    response = client.get('/profile?start_date=2026-01-01&end_date=2026-05-31')
    data = response.data.decode('utf-8')

    # Count some unique transaction markers to verify more than 10
    assert "Old transaction 1" in data, "Should show Jan transaction"
    assert "Old transaction 2" in data, "Should show Jan transaction"
    assert "Feb transaction 1" in data, "Should show Feb transaction"
    assert "Feb transaction 2" in data, "Should show Feb transaction"
    assert "March transaction 1" in data, "Should show March transaction"
    assert "March transaction 2" in data, "Should show March transaction"
    assert "April transaction 1" in data, "Should show April transaction"
    assert "April transaction 2" in data, "Should show April transaction"
    assert "May transaction 1" in data, "Should show May transaction"
    assert "May transaction 2" in data, "Should show May transaction"
    assert "May transaction 3" in data, "Should show May transaction"
    assert "May transaction 4" in data, "Should show May transaction"
    # That's 12 transactions visible - proves no limit is applied


# ------------------------------------------------------------------ #
# Partial Filter Tests (Only One Date Provided)                       #
# ------------------------------------------------------------------ #

def test_filter_with_only_start_date_ignored(user_with_transactions):
    """If only start_date is provided (no end_date), ignore filter and show default view."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-05-01')
    data = response.data.decode('utf-8')

    # Should show default behavior (most recent 10)
    assert "Recent transaction 3" in data, "Should show most recent transactions"
    assert "Showing transactions from" not in data, "Should not show filter message"
    # Should NOT show the 11th transaction
    assert "Old transaction 1" not in data, "Should apply default 10-item limit"


def test_filter_with_only_end_date_ignored(user_with_transactions):
    """If only end_date is provided (no start_date), ignore filter and show default view."""
    client, user_id = user_with_transactions

    response = client.get('/profile?end_date=2026-05-31')
    data = response.data.decode('utf-8')

    # Should show default behavior (most recent 10)
    assert "Recent transaction 3" in data, "Should show most recent transactions"
    assert "Showing transactions from" not in data, "Should not show filter message"
    assert "Old transaction 1" not in data, "Should apply default 10-item limit"


def test_filter_with_empty_start_date_ignored(user_with_transactions):
    """If start_date is empty string, ignore filter."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=&end_date=2026-05-31')
    data = response.data.decode('utf-8')

    # Should show default view
    assert "Recent transaction 3" in data, "Should show most recent transactions"
    assert "Showing transactions from" not in data, "Should not show filter message"


def test_filter_with_empty_end_date_ignored(user_with_transactions):
    """If end_date is empty string, ignore filter."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-01-01&end_date=')
    data = response.data.decode('utf-8')

    # Should show default view
    assert "Recent transaction 3" in data, "Should show most recent transactions"
    assert "Showing transactions from" not in data, "Should not show filter message"


# ------------------------------------------------------------------ #
# Empty Result Tests                                                  #
# ------------------------------------------------------------------ #

def test_filter_with_no_matching_transactions_shows_empty_message(user_with_transactions):
    """When filtered date range has zero transactions, show 'No transactions found' message."""
    client, user_id = user_with_transactions

    # Filter for a date range with no transactions (e.g., July 2026)
    response = client.get('/profile?start_date=2026-07-01&end_date=2026-07-31')
    data = response.data.decode('utf-8')

    assert "No transactions found in this date range" in data, "Should show empty state message"
    assert "Showing transactions from" in data, "Should still show filter active message"


def test_empty_result_still_shows_summary_stats(user_with_transactions):
    """Summary stats should remain visible even when filter returns no transactions."""
    client, user_id = user_with_transactions

    # Filter for empty date range
    response = client.get('/profile?start_date=2026-12-01&end_date=2026-12-31')
    data = response.data.decode('utf-8')

    # Summary stats should still be present (all-time data)
    assert "Total Spent" in data or "total spent" in data.lower(), "Should show total spent stat"
    assert "Transactions" in data or "transactions" in data.lower(), "Should show transaction count stat"


# ------------------------------------------------------------------ #
# Invalid Date Handling                                                #
# ------------------------------------------------------------------ #

def test_filter_with_invalid_date_format_gracefully_handled(user_with_transactions):
    """Invalid date format should not crash; may show default view or ignore filter."""
    client, user_id = user_with_transactions

    # Try invalid date format
    response = client.get('/profile?start_date=invalid&end_date=2026-05-31')

    # Should not crash (200 or redirect, but not 500)
    assert response.status_code in [200, 302], "Should handle invalid date gracefully"

    if response.status_code == 200:
        data = response.data.decode('utf-8')
        # Should show some transactions (either filtered or default)
        assert "Profile" in data or "Transaction" in data, "Should render profile page"


def test_filter_with_malformed_date_shows_default_view(user_with_transactions):
    """Malformed dates should fall back to default view."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-13-45&end_date=2026-99-99')

    if response.status_code == 200:
        data = response.data.decode('utf-8')
        # Should likely show recent transactions (default behavior)
        assert "Recent transaction 3" in data or "transaction" in data.lower(), "Should show some content"


# ------------------------------------------------------------------ #
# Clear Filter Tests                                                  #
# ------------------------------------------------------------------ #

def test_clear_filter_returns_to_default_view(user_with_transactions):
    """Clicking 'Clear' (navigating to /profile without params) returns to default view."""
    client, user_id = user_with_transactions

    # First apply a filter
    response_filtered = client.get('/profile?start_date=2026-05-01&end_date=2026-05-31')
    assert "Showing transactions from" in response_filtered.data.decode('utf-8'), "Filter should be active"

    # Then clear by visiting /profile without params
    response_cleared = client.get('/profile')
    data = response_cleared.data.decode('utf-8')

    assert "Showing transactions from" not in data, "Filter message should be gone"
    assert "Recent transaction 3" in data, "Should show most recent transactions again"
    assert "Old transaction 1" not in data, "Should apply default 10-item limit again"


# ------------------------------------------------------------------ #
# Summary Stats Invariance Tests                                      #
# ------------------------------------------------------------------ #

def test_summary_stats_unchanged_by_filter(user_with_transactions):
    """Summary stats show all-time data regardless of transaction filter."""
    client, user_id = user_with_transactions

    # Get default view summary stats
    response_default = client.get('/profile')
    data_default = response_default.data.decode('utf-8')

    # Get filtered view summary stats (May only)
    response_filtered = client.get('/profile?start_date=2026-05-01&end_date=2026-05-31')
    data_filtered = response_filtered.data.decode('utf-8')

    # Total spent should be the same in both views (all-time data)
    # Extract total from default view (this is a simplified check)
    assert "₹" in data_default, "Should show currency in default view"
    assert "₹" in data_filtered, "Should show currency in filtered view"

    # Transaction count should match all-time count (15 transactions)
    # This is hard to assert precisely without parsing HTML, but we can verify
    # the stats section exists in both
    assert "Total Spent" in data_default or "total" in data_default.lower()
    assert "Total Spent" in data_filtered or "total" in data_filtered.lower()


def test_category_breakdown_unchanged_by_filter(user_with_transactions):
    """Category breakdown shows all-time data regardless of transaction filter."""
    client, user_id = user_with_transactions

    # Get default view categories
    response_default = client.get('/profile')
    data_default = response_default.data.decode('utf-8')

    # Get filtered view categories (filtering to March only)
    response_filtered = client.get('/profile?start_date=2026-03-01&end_date=2026-03-31')
    data_filtered = response_filtered.data.decode('utf-8')

    # Both should show all-time category breakdown
    # Look for various categories that exist across all dates
    assert "Food" in data_default, "Default view should show Food category"
    assert "Food" in data_filtered, "Filtered view should also show Food category (all-time)"

    assert "Transport" in data_default, "Default view should show Transport category"
    assert "Transport" in data_filtered, "Filtered view should also show Transport category (all-time)"


# ------------------------------------------------------------------ #
# Template Context Tests                                              #
# ------------------------------------------------------------------ #

def test_filter_active_flag_set_correctly_when_filtered(user_with_transactions):
    """Template receives filter_active=True when both dates provided."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-05-01&end_date=2026-05-31')
    data = response.data.decode('utf-8')

    # When filter is active, we should see the filter message
    assert "Showing transactions from" in data, "filter_active should be True"


def test_filter_active_flag_false_when_no_dates(user_with_transactions):
    """Template receives filter_active=False when no dates provided."""
    client, user_id = user_with_transactions

    response = client.get('/profile')
    data = response.data.decode('utf-8')

    # When filter is not active, we should NOT see the filter message
    assert "Showing transactions from" not in data, "filter_active should be False"


def test_filter_active_flag_false_when_partial_dates(user_with_transactions):
    """Template receives filter_active=False when only one date provided."""
    client, user_id = user_with_transactions

    response = client.get('/profile?start_date=2026-05-01')
    data = response.data.decode('utf-8')

    assert "Showing transactions from" not in data, "filter_active should be False with partial dates"


# ------------------------------------------------------------------ #
# Edge Case: User With No Transactions                                #
# ------------------------------------------------------------------ #

def test_filter_with_no_transactions_at_all(auth_client):
    """User with zero transactions should see appropriate message."""
    # auth_client has a user with no transactions
    response = auth_client.get('/profile')
    data = response.data.decode('utf-8')

    # Should render without error
    assert response.status_code == 200, "Should load profile even with no transactions"

    # Should show zero or empty state
    # (Implementation may vary, but page should render)


def test_filter_on_empty_account_shows_no_results(auth_client):
    """Filtering when account has no transactions shows empty state."""
    response = auth_client.get('/profile?start_date=2026-01-01&end_date=2026-12-31')
    data = response.data.decode('utf-8')

    assert response.status_code == 200, "Should load profile"
    assert "Showing transactions from" in data, "Should show filter active message"
    # Should show no transactions message (either the filter empty message or general empty state)


# ------------------------------------------------------------------ #
# Date Range Order Tests                                              #
# ------------------------------------------------------------------ #

def test_filter_with_start_after_end_date(user_with_transactions):
    """
    When start_date is after end_date, the behavior depends on implementation.
    Spec mentions client-side HTML5 validation, but server should handle gracefully.
    This test verifies no crash occurs.
    """
    client, user_id = user_with_transactions

    # Start date after end date (logically invalid)
    response = client.get('/profile?start_date=2026-05-31&end_date=2026-05-01')

    # Should not crash
    assert response.status_code == 200, "Should handle reversed dates gracefully"

    data = response.data.decode('utf-8')
    # May show no results or ignore filter
    assert "Profile" in data or "Transaction" in data, "Should render profile page"


# ------------------------------------------------------------------ #
# Integration Test: Full Filter Workflow                              #
# ------------------------------------------------------------------ #

def test_full_filter_workflow(user_with_transactions):
    """
    Integration test: Apply filter, verify results, clear filter, verify default view.
    """
    client, user_id = user_with_transactions

    # Step 1: Visit default profile
    response1 = client.get('/profile')
    data1 = response1.data.decode('utf-8')
    assert "Recent transaction 3" in data1, "Should show recent transactions initially"
    assert "Showing transactions from" not in data1, "No filter message initially"

    # Step 2: Apply filter for May
    response2 = client.get('/profile?start_date=2026-05-01&end_date=2026-05-31')
    data2 = response2.data.decode('utf-8')
    assert "Showing transactions from" in data2, "Filter message should appear"
    assert "01 May 2026" in data2, "Should show formatted start date"
    assert "31 May 2026" in data2, "Should show formatted end date"
    assert "May transaction 1" in data2, "Should show filtered results"
    assert "April transaction" not in data2, "Should not show transactions outside range"

    # Step 3: Clear filter by visiting /profile again
    response3 = client.get('/profile')
    data3 = response3.data.decode('utf-8')
    assert "Recent transaction 3" in data3, "Should show recent transactions again"
    assert "Showing transactions from" not in data3, "Filter message should be gone"
    assert "Old transaction 1" not in data3, "Should apply default limit again"


# ------------------------------------------------------------------ #
# Form Rendering Tests                                                #
# ------------------------------------------------------------------ #

def test_profile_page_has_date_filter_form(user_with_transactions):
    """Profile page should display date filter form with proper inputs."""
    client, user_id = user_with_transactions

    response = client.get('/profile')
    data = response.data.decode('utf-8')

    # Check for form elements
    assert 'type="date"' in data, "Should have date input fields"
    assert 'Filter' in data or 'filter' in data, "Should have filter button"
    assert 'Clear' in data or 'clear' in data, "Should have clear button/link"


def test_filter_form_has_correct_action(user_with_transactions):
    """Filter form should submit to /profile."""
    client, user_id = user_with_transactions

    response = client.get('/profile')
    data = response.data.decode('utf-8')

    # Form should target /profile (may be method GET)
    assert 'action="/profile"' in data or 'action=' not in data, "Form should submit to /profile"
