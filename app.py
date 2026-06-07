from flask import Flask, render_template, request, redirect, url_for
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash

app = Flask(__name__)


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


@app.route("/login")
def login():
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
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
