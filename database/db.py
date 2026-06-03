import sqlite3
from werkzeug.security import generate_password_hash


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect("spendly.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_db():
    """Inserts sample data for development."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if users table already has data
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # Insert demo user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123"))
        )

        # Get the demo user's ID
        demo_user_id = cursor.lastrowid

        # Insert 8 sample expenses
        sample_expenses = [
            (demo_user_id, 450.50, "Food", "2026-06-02", "Grocery shopping at supermarket"),
            (demo_user_id, 85.00, "Transport", "2026-06-03", "Uber to office"),
            (demo_user_id, 1200.00, "Bills", "2026-06-01", "Monthly electricity bill"),
            (demo_user_id, 350.00, "Health", "2026-06-05", "Doctor consultation"),
            (demo_user_id, 800.00, "Entertainment", "2026-06-07", "Movie tickets and dinner"),
            (demo_user_id, 2500.00, "Shopping", "2026-06-10", None),
            (demo_user_id, 150.00, "Food", "2026-06-12", "Restaurant lunch"),
            (demo_user_id, 500.00, "Other", "2026-06-15", "Miscellaneous expenses"),
        ]

        cursor.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            sample_expenses
        )

        conn.commit()

    conn.close()
