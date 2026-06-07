# Spec: Registration

## Overview

The Registration feature implements user account creation for Spendly. Users can sign up with their name, email, and password. The system validates input, checks for duplicate emails, hashes passwords securely, and stores users in the database. On successful registration, users are redirected to the login page.

## Depends on

- **Step 1: Database Setup** — The users table with email uniqueness constraint must exist, and password hashing with werkzeug must be available.

## Routes

- `POST /register` — Process registration form submission (logged-out users only) — public

No other new routes; the GET `/register` route already exists and serves the form.

## Database changes

No database changes. The users table created in Step 1 is sufficient.

## Templates

**Create:** None.

**Modify:** 
- `templates/register.html` — Enhance the registration form to include proper error display and ensure it submits to `POST /register`

## Files to change

- `app.py` — Add the `POST /register` route handler

## Files to create

None.

## New dependencies

No new dependencies. werkzeug is already in requirements.txt.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw sqlite3 with parameterised queries only
- Passwords hashed with werkzeug's `generate_password_hash()`
- All form inputs must be validated on the server (email format, name length, password length)
- Email uniqueness must be checked before insertion; show "Email already in use" error if duplicate
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Store passwords — do NOT use plaintext or reversible encryption
- Successful registration redirects to `/login` with a success message or flash notification (simple approach: redirect only, user sees login form)
- Failed registration re-renders the form with inline error messages using the `.auth-error` class

## Definition of done

- [ ] User can enter name, email, and password in the registration form
- [ ] Form validation catches missing or invalid email addresses (e.g., no @ symbol)
- [ ] Form validation catches password shorter than 8 characters
- [ ] Form validation catches duplicate email and displays error: "Email already in use"
- [ ] Successful registration hashes password and stores user in database
- [ ] After successful registration, user is redirected to `/login`
- [ ] Existing passwords hash consistently (werkzeug doesn't produce identical hashes for the same password — only verification works)
- [ ] Error messages display inline on the form with `.auth-error` styling
- [ ] The register template uses `.auth-section`, `.auth-container`, and `.form-*` CSS classes per CLAUDE.md conventions
