# Spec: Login and Logout

## Overview

The Login and Logout feature implements user authentication for Spendly. Users can sign in with their email and password, which opens a session that persists across requests. The system validates credentials against the database using werkzeug's password verification, establishes a server-side session, and displays the user's name in the navbar. Logout clears the session and returns the user to the public state.

## Depends on

- **Step 1: Database Setup** — Users table with password_hash must exist
- **Step 2: Registration** — Users must be created with hashed passwords before they can log in

## Routes

- `POST /login` — Process login form submission (public, logged-out users only)
- `GET /logout` — Clear session and redirect to landing page (logged-in users only)

The GET `/login` route already exists and serves the form.

## Database changes

No database changes. The users table from Step 1 is sufficient.

## Templates

**Create:** None.

**Modify:**
- `templates/base.html` — Update navbar to show user's name and logout link when logged in; show login/register links when logged out
- `templates/login.html` — Ensure form submits to `POST /login` and displays errors

## Files to change

- `app.py` — Add session configuration, POST /login route handler, GET /logout route handler, and Jinja2 context processor
- `templates/base.html` — Conditional navbar links based on logged-in state

## Files to create

None.

## New dependencies

No new dependencies. Flask's `session` is built-in.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw sqlite3 with parameterised queries only
- Use werkzeug's `check_password_hash()` to verify passwords (never compare plaintext)
- Use Flask's `session` to store `user_id` after successful login
- Set a strong `SECRET_KEY` in app.py for session encryption (can use environment variable or generate one)
- All form inputs must be validated on the server
- Logout must clear the session using `session.clear()` and redirect to landing page
- Use a Jinja2 `@app.context_processor` to make `current_user` available in all templates
- Only authenticated users can access logout route
- Login form errors: "Invalid email or password" (generic for security), "Email is required", "Password is required"
- All templates extend `base.html`

## Definition of done

- [ ] User can enter email and password on login form
- [ ] Form validation catches missing email or password and displays error
- [ ] Invalid credentials display "Invalid email or password" error (no hint whether email exists or password wrong)
- [ ] Successful login creates a session with user_id and redirects to profile (or dashboard — TBD in Step 4)
- [ ] Navbar displays user's name and logout link when logged in
- [ ] Navbar displays login/register links when logged out
- [ ] Logout route clears session and redirects to landing page
- [ ] After logout, user is returned to public state (navbar shows login/register)
- [ ] Attempted access to logout without logged-in session redirects to login
- [ ] Session persists across page refreshes for logged-in user
- [ ] Closing browser or clearing cookies ends session
- [ ] Password verification uses werkzeug's `check_password_hash()` (not plaintext comparison)
