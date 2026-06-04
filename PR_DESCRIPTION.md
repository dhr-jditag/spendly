# feat: Add Expense Entry Form (Step 07)

## Summary

Implements Step 07: Add Expense feature, allowing logged-in users to create new expense records through a dedicated form page at `/expenses/add`.

## Changes

### Backend
- Added `insert_expense(user_id, amount, category, date, description)` helper in `database/queries.py`
- Replaced `/expenses/add` stub route with full GET+POST handler in `app.py`
- Implemented comprehensive validation:
  - Amount: must be positive number > 0
  - Category: must be one of 7 fixed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other)
  - Date: must be valid YYYY-MM-DD format
  - Description: optional, max 200 chars
- Authentication guard: redirects to login if not authenticated
- Error handling: re-renders form with error messages and pre-filled values on validation failure
- Success flow: redirects to profile with success flash message

### Frontend
- Created `templates/add_expense.html` with expense entry form
- Added "Add Expense" button to profile page transaction section
- Added "Add Expense" link to navbar (visible only when logged in)
- Mobile-responsive design for section header and button
- Uses CSS variables and extends `base.html`

### Spec
- Added `.claude/specs/07-add-expense.md` documenting feature requirements

## Testing

Manual testing completed successfully:
- ✅ Unauthenticated access redirects to `/login` (302)
- ✅ GET request shows form with all required fields
- ✅ POST with valid data inserts expense and redirects to profile
- ✅ Amount validation: zero/negative amounts rejected
- ✅ Amount validation: non-numeric input rejected
- ✅ Category validation: invalid categories rejected
- ✅ Date validation: invalid date formats rejected
- ✅ New expense appears in profile transactions list
- ✅ Navigation: navbar link and profile button both work

## Dependencies

No new dependencies added.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
