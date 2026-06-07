import sqlite3
import os
from werkzeug.security import generate_password_hash


def get_db():
    """Open a connection to the SQLite database with row_factory and foreign keys enabled."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    """Create all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()


def seed_db():
    """Insert sample data for development if not already present."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return

    # Insert demo user
    password_hash = generate_password_hash('demo123')
    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.com', password_hash)
    )
    user_id = cursor.lastrowid

    # Insert sample expenses
    expenses = [
        (user_id, 450.00, 'Food', '2026-06-01', 'Grocery run'),
        (user_id, 120.00, 'Transport', '2026-06-02', 'Metro card recharge'),
        (user_id, 850.00, 'Bills', '2026-06-03', 'Electricity bill'),
        (user_id, 600.00, 'Health', '2026-06-04', 'Pharmacy'),
        (user_id, 299.00, 'Entertainment', '2026-06-05', 'OTT subscription'),
        (user_id, 1200.00, 'Shopping', '2026-06-05', 'Clothes'),
        (user_id, 200.00, 'Other', '2026-06-06', 'Miscellaneous'),
        (user_id, 350.00, 'Food', '2026-06-07', 'Restaurant lunch'),
    ]

    cursor.executemany(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
        expenses
    )

    conn.commit()
    conn.close()
