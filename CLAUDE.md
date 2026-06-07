# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a personal expense tracking web application designed for Indian users. It allows users to log expenses, understand spending patterns, and stay within budget. The app emphasizes simplicity and speed with a focus on tracking expenses in Rupees.

- **Tech Stack:** Flask 3.1.3, Jinja2 templating, vanilla JavaScript (no frameworks), SQLite, CSS custom properties
- **Port:** 5001 (configured in app.py)
- **Design Language:** Minimalist with serif headings (DM Serif Display) and sans-serif body (DM Sans), green accent color (#1a472a)

## Getting Started

### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Development Server

```bash
python app.py
```

The app will be available at `http://localhost:5001`

### Project Structure

```
├── app.py                 # Flask application and route definitions
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css      # Global styles with CSS design system variables
│   └── js/
│       └── main.js        # Vanilla JavaScript utilities (e.g., modal handlers)
├── templates/
│   ├── base.html          # Base template with navbar, footer, shared structure
│   ├── landing.html       # Home page with hero, features, and CTA sections
│   ├── login.html         # Sign in form
│   ├── register.html      # Account creation form
│   ├── terms.html         # Terms and Conditions page
│   └── privacy.html       # Privacy Policy page
└── database/
    ├── __init__.py
    └── db.py              # Database initialization (stub — to be implemented)
```

## Architecture

### Frontend Architecture

**Template Structure:** All templates extend `base.html`, which provides:
- Navbar with branding and navigation links
- Main content area via `{% block content %}`
- Footer with links and branding
- Script injection point via `{% block scripts %}`

**Design System:** CSS variables defined in `:root` in `static/css/style.css`:
- **Colors:** `--ink` (text), `--paper` (background), `--accent` (green), `--accent-2` (orange), `--danger` (red)
- **Typography:** `--font-display` (serif for headings), `--font-body` (sans-serif)
- **Spacing:** `--radius-sm`, `--radius-md`, `--radius-lg` for border-radius
- **Layout:** `--max-width: 1200px` for content containers

**Page Patterns:**
- **Auth pages** (login/register): Use `.auth-section` container with centered `.auth-container` (440px wide)
- **Legal pages** (terms/privacy): Use `.cta-section` header followed by styled `.auth-card` content container
- **Landing page:** Hero section with grid layout, features grid (3 columns), CTA section

### Backend Architecture

**Routing:** Simple Flask routing with no database integration yet (placeholder routes exist for Steps 2–9):
- `GET /` → Landing page
- `GET /register` → Registration form
- `GET /login` → Login form
- `GET /terms` → Terms and Conditions
- `GET /privacy` → Privacy Policy
- Future routes (logout, profile, expense management) are stubbed with placeholder responses

**Database Layer:** Stub file at `database/db.py` — students implement SQLite connection management and schema creation.

### JavaScript

**No external frameworks** — all JavaScript is vanilla (no jQuery, React, Vue, etc.).

Current utilities:
- **Video Modal Handler** (`main.js`): Manages opening/closing of YouTube embed modal on landing page
  - `openVideoModal()` — sets iframe src and shows modal
  - `closeVideoModal()` — hides modal and clears iframe src (stops playback)
  - Supports three close mechanisms: close button, outside-modal click (backdrop), Escape key

## Development Workflow

### Making Changes

1. **Templates:** Modify Jinja2 files in `templates/` and refresh browser
2. **Styles:** Edit `static/css/style.css` — use design system variables, not hardcoded colors
3. **JavaScript:** Edit `static/js/main.js` — keep vanilla, avoid frameworks
4. **Routes:** Add new routes to `app.py` and corresponding templates

### Testing Changes Locally

- Flask debug mode is enabled (`app.run(debug=True)`)
- Server auto-reloads on file changes
- Open `http://localhost:5001` in browser

### Git Workflow

Commit messages follow a pattern: `<section>: <description>`
- Example: `landing: add youtube modal on see how it works click`
- Sections: landing, auth, footer, etc.

## Key Patterns & Conventions

### CSS Classes

**Buttons:**
- `.btn-primary` — dark filled button (hovers to green)
- `.btn-ghost` — outlined button
- `.btn-submit` — full-width form submit button

**Forms:**
- `.form-group` — wrapper for label + input
- `.form-input` — text/email/password input styling
- `.auth-error` — error message display

**Layout:**
- `.hero`, `.features`, `.cta-section` — major page sections
- `*-inner` classes (`.hero-inner`, `.features-inner`, etc.) — max-width constraint containers
- `.nav-inner`, `.auth-container` — consistent padding and max-width handling

**Modals:**
- `.modal` — fixed overlay (hidden by default, shown with `.show` class)
- `.modal-content` — card styling
- `.modal-close` — close button

### Template Patterns

**Block structure in base.html:**
```html
{% block title %}  <!-- Page title in <title> tag -->
{% block head %}   <!-- Optional: per-page styles/meta -->
{% block content %} <!-- Main page content -->
{% block scripts %} <!-- Optional: per-page scripts -->
```

**Form pattern (login/register):**
```html
<form method="POST" action="/route">
    {% if error %}<div class="auth-error">{{ error }}</div>{% endif %}
    <div class="form-group">
        <label for="field">Label</label>
        <input type="text" id="field" name="field" class="form-input" required>
    </div>
    <button type="submit" class="btn-submit">Submit</button>
</form>
```

### Color Usage

- **Text:** `--ink` (dark) for primary, `--ink-muted` for secondary
- **Backgrounds:** `--paper` (main), `--paper-warm` (section variants), `--paper-card` (cards)
- **Accents:** `--accent` (#1a472a green) for interactive elements, `--accent-2` (#c17f24 orange) for secondary highlights
- **Danger:** `--danger` (#c0392b red) for warnings/errors

Avoid hardcoding colors — use CSS variables so design system updates propagate.

## Common Tasks

### Add a New Page

1. Create `templates/new-page.html` extending `base.html`
2. Add route in `app.py`: `@app.route("/new-page")` → `return render_template("new-page.html")`
3. Link from navbar or other pages using `{{ url_for('new_page') }}`
4. Style using existing CSS classes or add new styles to `style.css` using design system variables

### Add Form Validation

Currently, HTML5 validation only (required, type attributes). Backend validation is stubbed — will be implemented in later steps.

### Modify the Landing Page

The landing page is the main entry point. Structure:
1. **Hero Section:** `.hero` grid with text + mock card visual
2. **Features Section:** `.features` with 3-column grid of feature cards
3. **CTA Section:** `.cta-section` final call-to-action
4. **Video Modal:** Hidden modal triggered by "See how it works" button

When modifying, maintain responsive behavior (`@media (max-width: 900px)` and `max-width: 600px`).

## Notes for Future Work

- **Database Integration:** The `database/db.py` stub needs implementation for SQLite connection management and schema
- **Authentication:** Login/register routes exist but don't process forms — will be implemented later
- **Expense Management:** Placeholder routes exist for add/edit/delete expense workflows
- **Testing:** `pytest` and `pytest-flask` are in requirements but no tests exist yet
- **Environment Variables:** `.env` is gitignored — use for secrets (database path, Flask secret key, etc.)
- **Mobile Responsive:** Design includes `@media` queries; test on smaller screens before committing
