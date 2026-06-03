# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is an expense tracking web application built with Flask. The project appears to be a teaching/learning codebase with placeholder routes and stub files that students will implement incrementally through a multi-step curriculum.

The app currently has a landing page, registration/login pages, and terms/privacy pages. Core expense management features (add, edit, delete) are defined as placeholder routes that return stub messages indicating future implementation steps.

## Architecture

### Application Structure

- **`app.py`**: Main Flask application entry point
  - Defines all routes (both implemented and placeholder)
  - Runs on port 5001 in debug mode
  - Routes are organized into two sections: fully implemented pages and placeholder routes for student implementation

- **`database/`**: Database layer (to be implemented)
  - `db.py`: Placeholder for SQLite database utilities (`get_db()`, `init_db()`, `seed_db()`)
  - `__init__.py`: Package initialization

- **`templates/`**: Jinja2 HTML templates
  - `base.html`: Base template with navbar, footer, and common layout
  - `landing.html`: Marketing landing page with hero section, features, CTA, and embedded YouTube modal
  - `register.html`, `login.html`: Authentication pages
  - `terms.html`, `privacy.html`: Legal pages

- **`static/`**: Static assets
  - `css/style.css`: Application styles
  - `js/main.js`: JavaScript (currently minimal placeholder)

### Template Inheritance

All pages extend `base.html` which provides:
- Navigation bar with brand icon (◈) and "Spendly" branding
- Sign in / Get started links
- Footer with terms and privacy policy links
- Google Fonts (DM Serif Display, DM Sans)

Pages override `{% block title %}`, `{% block content %}`, and optionally `{% block scripts %}`.

### Landing Page Features

The landing page (`landing.html`) includes:
- Hero section with mock dashboard visualization showing stats and category breakdowns
- YouTube video modal (opens on "See how it works" click, currently uses placeholder video URL)
- Features section highlighting key functionality
- CTA section encouraging registration

## Development Commands

### Running the Application

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask development server
python app.py
```

The app will be available at `http://localhost:5001` (note: uses port 5001, not the default 5000).

### Testing

pytest and pytest-flask are included in requirements, but no tests exist yet:

```bash
# Run tests (when implemented)
pytest

# Run specific test file
pytest test_<name>.py
```

## Key Implementation Notes

### Database Layer (To Be Implemented)

The `database/db.py` file needs three functions:
- `get_db()`: Return SQLite connection with `row_factory` enabled and foreign keys ON
- `init_db()`: Create tables using `CREATE TABLE IF NOT EXISTS`
- `seed_db()`: Insert sample development data

### Placeholder Routes

These routes return stub messages and need implementation:
- `/logout` (Step 3)
- `/profile` (Step 4)
- `/expenses/add` (Step 7)
- `/expenses/<int:id>/edit` (Step 8)
- `/expenses/<int:id>/delete` (Step 9)

When implementing these, remember to add corresponding templates and update the database layer.

### Currency

The application uses Indian Rupees (₹) as the display currency throughout the UI.

## Python Environment

- Python 3.x
- Flask 3.1.3
- Werkzeug 3.1.6
- Virtual environment in `venv/` directory (already set up)
