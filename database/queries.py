import sqlite3
from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    """Returns user info dict with name, email, and member_since formatted as 'Month YYYY'."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        # Parse created_at and format as "Month YYYY"
        try:
            # Try full datetime format first
            created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Fallback to date-only format
                created = datetime.strptime(row["created_at"], "%Y-%m-%d")
            except ValueError:
                # If parsing fails, use current date as fallback
                created = datetime.now()

        member_since = created.strftime("%B %Y")

        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": member_since
        }
    finally:
        conn.close()


def get_summary_stats(user_id):
    """Returns summary statistics dict with total_spent, transaction_count, and top_category."""
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Query 1: Get total spent and transaction count
        cursor.execute("SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        # Handle NULL from SUM when no expenses exist
        total_spent = row["total"] or 0
        transaction_count = row["count"]

        # Query 2: Get top spending category
        cursor.execute("""
            SELECT category, SUM(amount) as category_total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY category_total DESC
            LIMIT 1
        """, (user_id,))
        category_row = cursor.fetchone()

        # If no expenses, use em dash as placeholder
        top_category = category_row["category"] if category_row else "—"

        return {
            "total_spent": float(total_spent),
            "transaction_count": transaction_count,
            "top_category": top_category
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    """Returns list of recent transaction dicts with formatted dates.

    If start_date and end_date are provided, returns ALL transactions in that range.
    Otherwise, returns the most recent transactions up to the limit.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Build query based on whether date filtering is active
        if start_date and end_date:
            # Show all transactions within date range (no limit)
            cursor.execute(
                "SELECT date, description, category, amount FROM expenses WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date DESC, id DESC",
                (user_id, start_date, end_date)
            )
        else:
            # Show most recent transactions with limit
            cursor.execute(
                "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
                (user_id, limit)
            )

        rows = cursor.fetchall()

        transactions = []
        for row in rows:
            # Parse date from "YYYY-MM-DD" to "DD Mon YYYY"
            parsed_date = datetime.strptime(row["date"], "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%d %b %Y")

            # Handle NULL description
            description = row["description"] if row["description"] else "—"

            transactions.append({
                "date": formatted_date,
                "description": description,
                "category": row["category"],
                "amount": row["amount"]
            })

        return transactions
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Returns list of category dicts with name, amount, and percentage."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC
        """, (user_id,))
        rows = cursor.fetchall()

        # Calculate grand total
        grand_total = sum(row["total"] for row in rows)

        # Handle edge cases: no expenses or zero total
        if grand_total == 0 or not rows:
            return []

        # Build category list with percentages
        categories = []
        for row in rows:
            pct = (row["total"] / grand_total) * 100
            pct = round(pct)
            categories.append({
                "name": row["category"],
                "amount": row["total"],
                "pct": pct
            })

        # Adjust percentages to sum to exactly 100
        total_pct = sum(c["pct"] for c in categories)
        if total_pct != 100 and categories:
            diff = 100 - total_pct
            categories[0]["pct"] += diff  # Adjust the largest (first) category

        return categories
    finally:
        conn.close()


def insert_expense(user_id, amount, category, date, description):
    """Inserts a new expense record and returns the new expense ID."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
