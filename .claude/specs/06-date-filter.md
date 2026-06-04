# Spec: Date Filter for Profile Page

## Overview
This feature adds date range filtering to the Recent Transactions section on the profile page. Users can select a date range (start and end dates) to view transactions within that period. The filter includes a form with two date inputs and a "Filter" button, plus a "Clear" button to reset to showing all transactions. This allows users to focus on specific time periods when reviewing their spending history.

## Depends on
- Step 1: Database setup (expenses table exists with date column)
- Step 2: Registration (user accounts exist)
- Step 3: Login + Logout (session management works)
- Step 4: Profile page (UI layout exists)
- Step 5: Backend routes for profile page (live database queries work)

## Routes
- `GET /profile` — modified to accept optional query parameters `start_date` and `end_date`; filters transactions if both are present

No new routes needed.

## Database changes
No database changes. The `expenses.date` column already exists and stores dates in `YYYY-MM-DD` format.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date filter form above the transaction history table
  - Form contains:
    - Label "Filter by Date Range"
    - Start date input (type="date")
    - End date input (type="date")
    - "Filter" submit button
    - "Clear" link/button that resets to `/profile` without query params
  - Display active filter state when dates are applied (e.g., "Showing transactions from DD Mon YYYY to DD Mon YYYY")
  - Update section title from "Recent Transactions" to "Transactions" since filtered view may show more or fewer than 10

## Files to change
- `app.py` — modify the `/profile` route to:
  - Read `start_date` and `end_date` from `request.args`
  - Pass these values to a modified `get_recent_transactions()` call
  - Pass filter state to the template for display
- `database/queries.py` — modify `get_recent_transactions()` to:
  - Accept optional `start_date` and `end_date` parameters
  - Add SQL WHERE clauses when dates are provided
  - Remove the LIMIT parameter when filtering (show ALL transactions in range, not just 10)
- `templates/profile.html` — add filter form and active filter display

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Date inputs must use HTML5 `type="date"` for native date picker
- When no dates are selected, show the most recent 10 transactions (existing behaviour)
- When dates are selected, show ALL transactions within that range (no limit)
- Date comparison in SQL must be inclusive: `date >= start_date AND date <= end_date`
- Both start_date and end_date must be provided for filtering to apply; if only one is present, ignore both and show default view
- Date inputs in the form should be pre-filled with the current filter values when filtering is active
- "Clear" action redirects to `/profile` with no query parameters
- If the date range returns zero transactions, display "No transactions found in this date range" message in the table

## Definition of done
- [ ] Visiting `/profile` without date parameters shows the most recent 10 transactions (existing behaviour preserved)
- [ ] The date filter form appears above the transaction history table
- [ ] Submitting the form with both start and end dates redirects to `/profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- [ ] Filtered view shows all transactions within the date range (not limited to 10)
- [ ] Filtered view displays "Showing transactions from DD Mon YYYY to DD Mon YYYY" message
- [ ] Date inputs in the form are pre-filled with current filter values when active
- [ ] Clicking "Clear" removes the filter and returns to default view showing most recent 10 transactions
- [ ] If the filtered date range has zero transactions, the message "No transactions found in this date range" appears
- [ ] Summary stats and category breakdown remain unchanged (always show all-time data, regardless of transaction filter)
- [ ] Form validation: start_date must be less than or equal to end_date (client-side via HTML5, server-side graceful handling)
