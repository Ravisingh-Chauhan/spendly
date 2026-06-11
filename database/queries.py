from database.db import get_db
from datetime import datetime


def get_user_by_id(user_id):
    """
    Fetch user info by ID.
    Returns: dict with keys 'name', 'email', 'member_since' or None if not found
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, email, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    # Format member_since as "Month YYYY" (e.g., "January 2026")
    created_at_dt = datetime.fromisoformat(user['created_at'])
    member_since = created_at_dt.strftime('%B %Y')

    return {
        'name': user['name'],
        'email': user['email'],
        'member_since': member_since
    }


def get_summary_stats(user_id, date_from=None, date_to=None):
    """
    Calculate summary stats for a user, optionally filtered by date range.
    Returns: dict with keys 'total_spent' (float), 'transaction_count' (int), 'top_category' (str)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Build WHERE clause with optional date filtering
    where = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)

    # Get expenses for user
    cursor.execute(f'SELECT amount, category FROM expenses {where} ORDER BY date DESC', params)
    expenses = cursor.fetchall()
    conn.close()

    if not expenses:
        return {
            'total_spent': 0,
            'transaction_count': 0,
            'top_category': '—'
        }

    # Calculate total spent
    total_spent = sum(float(e['amount']) for e in expenses)

    # Count transactions
    transaction_count = len(expenses)

    # Find top category (by frequency)
    category_counts = {}
    for expense in expenses:
        category_counts[expense['category']] = category_counts.get(expense['category'], 0) + 1
    top_category = max(category_counts, key=category_counts.get)

    return {
        'total_spent': total_spent,
        'transaction_count': transaction_count,
        'top_category': top_category
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """
    Fetch recent transactions for a user, ordered newest first, optionally filtered by date range.
    Returns: list of dicts, each with keys 'date', 'description', 'category', 'amount'
    """
    conn = get_db()
    cursor = conn.cursor()

    # Build WHERE clause with optional date filtering
    where = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)
    params.append(limit)

    cursor.execute(
        f'SELECT date, description, category, amount FROM expenses {where} ORDER BY date DESC LIMIT ?',
        params
    )
    expenses = cursor.fetchall()
    conn.close()

    transactions = []
    for expense in expenses:
        transactions.append({
            'date': expense['date'],
            'description': expense['description'],
            'category': expense['category'],
            'amount': float(expense['amount'])
        })

    return transactions


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """
    Get per-category totals and percentages, optionally filtered by date range.
    Returns: list of dicts, each with keys 'name', 'amount', 'pct' (percentage, int)
    Percentages are guaranteed to sum to 100 (largest category absorbs rounding remainder).
    """
    conn = get_db()
    cursor = conn.cursor()

    # Build WHERE clause with optional date filtering
    where = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)

    cursor.execute(
        f'SELECT category, SUM(amount) as total FROM expenses {where} GROUP BY category ORDER BY total DESC',
        params
    )
    categories = cursor.fetchall()
    conn.close()

    if not categories:
        return []

    # Calculate total and percentages
    total_spent = sum(float(c['total']) for c in categories)

    breakdown = []
    calculated_pcts = []

    for i, category in enumerate(categories):
        amount = float(category['total'])
        pct = round(100 * amount / total_spent) if total_spent > 0 else 0

        breakdown.append({
            'name': category['category'],
            'amount': amount,
            'pct': pct
        })
        calculated_pcts.append(pct)

    # Adjust largest category to ensure percentages sum to 100
    if breakdown:
        pct_sum = sum(calculated_pcts)
        if pct_sum != 100:
            adjustment = 100 - pct_sum
            breakdown[0]['pct'] += adjustment

    return breakdown
