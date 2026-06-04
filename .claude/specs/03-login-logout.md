# Spec: Login and Logout

## Overview
This feature implements user authentication with login and logout functionality. Users can log in using their email and password credentials, which are validated against the database. On successful login, a session is created to keep the user authenticated across requests, and the user is redirected to a profile page. Users can log out to terminate their session. The navbar dynamically shows the user's name and logout link when logged in, or sign in/register links when logged out. This is the third step in the Spendly roadmap and enables user-specific functionality in future features.

## Depends on
- Step 01: Database Setup — requires the `users` table and `get_db()` function
- Step 02: Registration — requires users to exist in the database

## Routes
- `POST /login` — processes login form submission, validates credentials, creates session — public
- `GET /logout` — terminates user session, redirects to landing page — logged-in only

The existing `GET /login` route already renders the login form and requires no changes.

## Database changes
No database changes. Uses the existing `users` table with `email` and `password_hash` columns.

## Templates
- **Create:** `templates/profile.html` — basic profile page that extends `base.html` showing welcome message
- **Modify:** 
  - `templates/login.html` — update to use flash messages for errors
  - `templates/base.html` — update navigation to show user's name and "Logout" link when logged in, "Sign in" / "Get started" when logged out

## Files to change
- `app.py` — add `POST /login` route handler, implement `/logout` route, update `/profile` to render template, import `check_password_hash`
- `database/db.py` — add `get_user_by_email(email)` helper function
- `templates/base.html` — conditionally render navbar based on session state
- `templates/login.html` — use flash messages instead of inline errors

## Files to create
- `templates/profile.html` — basic profile page with welcome message

## New dependencies
No new dependencies. Uses existing packages:
- `werkzeug.security.check_password_hash` for password verification
- Flask `session` for storing user authentication state

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQL with `sqlite3`
- Parameterised queries only — never use string formatting in SQL
- Passwords must be verified with `werkzeug.security.check_password_hash`
- Store user information in Flask session on successful login: `session['user_id']`, `session['user_name']`, `session['user_email']`
- Email lookup should be case-insensitive (normalize to lowercase)
- Login errors should not reveal whether email exists (use generic "Invalid email or password" message)
- Use flash messages for login errors
- Logout must clear the session with `session.clear()`
- After successful login, redirect to `/profile` 
- After logout, redirect to `/` (landing page)
- If user is already logged in (session exists), redirect to `/profile` when accessing `/login` or `/register`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_user_by_email()` helper belongs in `database/db.py`

## Definition of done
- [ ] Navigate to `/login` and the form displays correctly
- [ ] Log in with valid demo user credentials (demo@spendly.com / demo123) — redirected to `/profile` page
- [ ] Profile page displays with welcome message and navbar shows user's name and "Logout" link
- [ ] After successful login, navbar shows user's name and "Logout" link instead of "Sign in" / "Get started"
- [ ] Try logging in with invalid email — shows "Invalid email or password" flash message
- [ ] Try logging in with valid email but wrong password — shows "Invalid email or password" flash message
- [ ] Click "Logout" link — session cleared, redirected to landing page, navbar shows "Sign in" / "Get started" again
- [ ] After logout, navbar reverts to showing "Sign in" and "Get started"
- [ ] Flask session contains `user_id`, `user_name`, and `user_email` after successful login
- [ ] When logged in, accessing `/login` or `/register` redirects to `/profile`
- [ ] After logout, `/login` and `/register` are accessible again