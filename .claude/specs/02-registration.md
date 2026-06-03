# Spec: Registration

## Overview
This feature implements user registration functionality, allowing new users to create accounts by providing their name, email, and password. The registration form validates input, checks for duplicate emails, securely hashes passwords using werkzeug, and creates a new user record in the database. Upon successful registration, users are redirected to the login page. This is the second step in the Spendly roadmap and establishes the foundation for user authentication.

## Depends on
- Step 01: Database Setup — requires the `users` table and `get_db()` function

## Routes
- `POST /register` — processes registration form submission, validates input, creates user account — public

The existing `GET /register` route already renders the registration form and requires no changes.

## Database changes
No database changes. The `users` table already exists with the required schema from Step 01.

## Templates
- **Create:** None
- **Modify:** 
  - `templates/register.html` — ensure form `method="POST"` and `action="/register"` are set (already present)

## Files to change
- `app.py` — add `POST /register` route handler with validation and user creation logic

## Files to create
None

## New dependencies
No new dependencies. Uses existing packages:
- `werkzeug.security.generate_password_hash` (already imported in `database/db.py`)
- Flask `request`, `redirect`, `url_for`, `flash`, `session` modules

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQL with `sqlite3`
- Parameterised queries only — never use string formatting in SQL
- Passwords must be hashed with `werkzeug.security.generate_password_hash` before storing
- Password minimum length: 8 characters
- Email validation: basic format check (contains @ and .)
- Name validation: must not be empty or whitespace-only
- Check for duplicate email before insertion — return error if email exists
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Flash messages for errors should use category 'error'
- On successful registration, redirect to `/login` with a success flash message
- Do not auto-login users after registration — they must explicitly log in

## Definition of done
- [ ] Navigate to `/register` and the form displays correctly
- [ ] Submit form with valid data (name, email, password ≥8 chars) — user created in database
- [ ] After successful registration, redirected to `/login` with success message
- [ ] Try registering with the same email twice — second attempt shows error message
- [ ] Try submitting with empty name — error message displayed
- [ ] Try submitting with invalid email format — error message displayed
- [ ] Try submitting with password <8 characters — error message displayed
- [ ] Check database — password is hashed (not stored in plain text)
- [ ] Register a new user, then verify they can log in (prerequisite: Step 03 Login must be complete)
