from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email
import sqlite3

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

    # Hardcoded user info
    user_info = {
        "name": session.get("user_name", "User"),
        "email": session.get("user_email", "user@example.com"),
        "member_since": "May 2026"
    }

    # Hardcoded summary stats
    summary_stats = {
        "total_spent": 45230.50,
        "transaction_count": 24,
        "top_category": "Food & Dining"
    }

    # Hardcoded transaction history
    transactions = [
        {"date": "01 Jun 2026", "description": "Dinner at The Olive Garden", "category": "Food & Dining", "amount": 1850.00},
        {"date": "31 May 2026", "description": "Uber ride to office", "category": "Transport", "amount": 320.00},
        {"date": "30 May 2026", "description": "Monthly Netflix subscription", "category": "Entertainment", "amount": 649.00},
        {"date": "28 May 2026", "description": "Grocery shopping at BigBasket", "category": "Food & Dining", "amount": 2450.00},
        {"date": "25 May 2026", "description": "New headphones", "category": "Shopping", "amount": 3499.00},
        {"date": "22 May 2026", "description": "Electricity bill", "category": "Bills", "amount": 1850.00}
    ]

    # Hardcoded category breakdown
    categories = [
        {"name": "Food & Dining", "amount": 12850.00, "percentage": 85},
        {"name": "Transport", "amount": 8450.00, "percentage": 70},
        {"name": "Shopping", "amount": 6230.00, "percentage": 55},
        {"name": "Entertainment", "amount": 4200.00, "percentage": 40},
        {"name": "Bills", "amount": 3500.00, "percentage": 30}
    ]

    return render_template(
        "profile.html",
        user_info=user_info,
        summary_stats=summary_stats,
        transactions=transactions,
        categories=categories
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
