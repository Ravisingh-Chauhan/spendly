from flask import Flask, render_template, request, redirect, url_for, session
from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'


# ------------------------------------------------------------------ #
# Jinja2 Context Processor                                            #
# ------------------------------------------------------------------ #

@app.context_processor
def inject_user():
    """Make current_user available in all templates."""
    user = None
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
    return dict(current_user=user)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None

        # Validate name
        if not name:
            error = "Name is required"
        elif len(name) < 2 or len(name) > 100:
            error = "Name must be between 2 and 100 characters"

        # Validate email
        if not error:
            if not email:
                error = "Email is required"
            elif "@" not in email:
                error = "Email must contain @"

        # Validate password
        if not error:
            if not password:
                error = "Password is required"
            elif len(password) < 8:
                error = "Password must be at least 8 characters"

        # Check email uniqueness
        if not error:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                error = "Email already in use"
            conn.close()

        # Insert user if no errors
        if not error:
            try:
                conn = get_db()
                cursor = conn.cursor()
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )
                conn.commit()
                conn.close()
                return redirect(url_for("login"))
            except Exception as e:
                error = "An error occurred during registration. Please try again."
                conn.close()

        return render_template("register.html", error=error)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None

        # Validate inputs
        if not email:
            error = "Email is required"
        elif not password:
            error = "Password is required"

        # Check credentials if no validation errors
        if not error:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                return redirect(url_for('profile'))
            else:
                error = "Invalid email or password"

        return render_template("login.html", error=error)

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
    return redirect(url_for('landing'))


@app.route("/profile")
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch real data from database
    user = get_user_by_id(user_id)
    if not user:
        return redirect(url_for('login'))

    stats = get_summary_stats(user_id)
    transactions = get_recent_transactions(user_id)
    categories = get_category_breakdown(user_id)

    # Prepare user_info dict with initials
    initials = ''.join([word[0].upper() for word in user['name'].split()])[:2]
    user_info = {
        'initials': initials,
        'name': user['name'],
        'email': user['email'],
        'member_since': user['member_since']
    }

    # Format stats for display (convert numbers to currency strings)
    stats_display = {
        'total_spent': f"₹{stats['total_spent']:,.2f}",
        'transaction_count': stats['transaction_count'],
        'top_category': stats['top_category']
    }

    # Format transactions for display
    transactions_display = []
    for txn in transactions:
        # Format date from "YYYY-MM-DD" to "Month DD"
        date_obj = datetime.strptime(txn['date'], '%Y-%m-%d')
        formatted_date = date_obj.strftime('%B %-d' if hasattr(date_obj, 'strftime') else '%B %d').replace(' 0', ' ')

        transactions_display.append({
            'date': formatted_date,
            'description': txn['description'],
            'category': txn['category'],
            'amount': f"₹{txn['amount']:,.2f}"
        })

    # Format categories for display
    categories_display = []
    for cat in categories:
        categories_display.append({
            'name': cat['name'],
            'total': f"₹{cat['amount']:,.2f}",
            'percentage': cat['pct']
        })

    return render_template('profile.html',
                         user_info=user_info,
                         stats=stats_display,
                         transactions=transactions_display,
                         categories=categories_display)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
