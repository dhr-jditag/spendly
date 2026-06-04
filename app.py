from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    insert_expense
)
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, redirect to profile
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name:
            return render_template("register.html", error="Name is required")

        if not email or "@" not in email or "." not in email:
            return render_template("register.html", error="Please enter a valid email address")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters")

        conn = get_db()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return render_template("register.html", error="Email already registered. Please log in.")

            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            conn.rollback()
            return render_template("register.html", error="Email already registered. Please log in.")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect to profile
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Authentication guard
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Extract date filter parameters from query string
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Only apply filter if both dates are present
    filter_active = bool(start_date and end_date)

    # Fetch live data from database
    user_info = get_user_by_id(user_id)
    summary_stats = get_summary_stats(user_id)

    if filter_active:
        transactions = get_recent_transactions(user_id, start_date=start_date, end_date=end_date)
    else:
        transactions = get_recent_transactions(user_id, limit=10)

    categories = get_category_breakdown(user_id)

    # Handle case where user not found (shouldn't happen if session is valid)
    if user_info is None:
        flash("User not found", "error")
        return redirect(url_for("logout"))

    # Format dates for display if filter is active
    start_date_formatted = None
    end_date_formatted = None
    if filter_active:
        try:
            from datetime import datetime
            start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d %b %Y")
            end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            # Invalid date format, ignore formatting
            pass

    return render_template(
        "profile.html",
        user_info=user_info,
        summary_stats=summary_stats,
        transactions=transactions,
        categories=categories,
        filter_active=filter_active,
        start_date=start_date,
        end_date=end_date,
        start_date_formatted=start_date_formatted,
        end_date_formatted=end_date_formatted
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    # Authentication guard
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Define valid categories
    VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

    if request.method == "POST":
        # Extract form data
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        # Convert empty description to None
        if not description:
            description = None

        # Validation
        error = None

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                error = "Amount must be greater than zero"
        except (ValueError, TypeError):
            error = "Please enter a valid amount"

        # Validate category
        if not error and category not in VALID_CATEGORIES:
            error = "Please select a valid category"

        # Validate date
        if not error:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                error = "Please enter a valid date"

        # If validation failed, re-render form with error and previous values
        if error:
            return render_template(
                "add_expense.html",
                error=error,
                amount=amount_str,
                category=category,
                date=date,
                description=description,
                categories=VALID_CATEGORIES,
                today=datetime.now().strftime("%Y-%m-%d")
            )

        # Insert expense
        try:
            user_id = session["user_id"]
            insert_expense(user_id, amount, category, date, description)
            flash("Expense added successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            return render_template(
                "add_expense.html",
                error="Failed to save expense. Please try again.",
                amount=amount_str,
                category=category,
                date=date,
                description=description,
                categories=VALID_CATEGORIES,
                today=datetime.now().strftime("%Y-%m-%d")
            )

    # GET request - render form with today's date as default
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "add_expense.html",
        categories=VALID_CATEGORIES,
        today=today
    )


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
