# Banking App — Full-Stack Build Plan

Reference documents:
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
- [`STEP_BY_STEP_IMPLEMENTATION_GUIDE.md`](STEP_BY_STEP_IMPLEMENTATION_GUIDE.md)

---

## Top-Level Overview

Build a complete two-tier banking web application:
- **Frontend:** Static HTML + Bootstrap 5 (CDN) in `FRONTEND/`
- **Backend:** Python 3.11 + Flask in `BACKEND/`
- **Database:** SQLite via Python `sqlite3` module (`BACKEND/banking.db`)
- **Tests:** pytest unit + integration tests in `tests/`

Features: Customer Login · Dashboard · View Balance · Deposit · Withdraw · Logout

The application must run locally with `python app.py` from inside `BACKEND/`.

---

## Sub-Task 1 — Project Scaffolding & Requirements File

**Intent:** Create the folder skeleton and `requirements.txt` so every subsequent sub-task has a known home for its files and dependencies can be installed in one command.

**Expected Outcomes:**
- Folders exist: `FRONTEND/`, `FRONTEND/static/`, `BACKEND/`, `tests/unit/`, `tests/integration/`
- `BACKEND/requirements.txt` lists Flask, Werkzeug, pytest
- `BACKEND/.gitignore` excludes `venv/`, `__pycache__/`, `*.pyc`, `*.db`, `.pytest_cache/`
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` created (empty, needed by pytest)

**Todo List:**
1. Create all folder placeholders (`.gitkeep` or `__init__.py` as appropriate)
2. Write `BACKEND/requirements.txt` with pinned-enough versions: `Flask>=3.0`, `pytest>=8.0`
3. Write `BACKEND/.gitignore`

**Status:** [ ] pending

---

## Sub-Task 2 — Database Layer (`models.py`)

**Intent:** Build the single source of truth for all SQLite operations. This must be complete before services or routes can be written.

**Expected Outcomes:**
- `BACKEND/models.py` exists with `init_db(db_path)`, `get_customer_by_username`, `get_balance`, `update_balance`
- `init_db` creates a `customers` table (id, full_name, username, password_hash, balance) if not present
- `init_db` seeds 3 demo accounts (alice/password123, bob/password456, carol/password789) with $1000 starting balance if table is empty
- Passwords are stored using `werkzeug.security.generate_password_hash`
- All functions accept `db_path` as a parameter (no global state) for testability
- `row_factory = sqlite3.Row` used so rows are addressable by column name

**Todo List:**
1. Write `BACKEND/models.py` with all four functions
2. Ensure `init_db` is idempotent (safe to call on every app start)

**Status:** [ ] pending

---

## Sub-Task 3 — Service Layer (`services.py`)

**Intent:** Isolate all business logic and validation from the HTTP layer. Services are the only layer that enforces rules about amounts, balances, and credential correctness.

**Expected Outcomes:**
- `BACKEND/services.py` exists with four functions
- `authenticate(db_path, username, password)` → `{"ok": True, "id": ..., "name": ...}` or `{"ok": False, "error": "..."}`
- `fetch_balance(db_path, customer_id)` → `{"ok": True, "balance": ...}` or `{"ok": False, "error": "..."}`
- `process_deposit(db_path, customer_id, amount)` → `{"ok": True, "balance": ...}` or `{"ok": False, "error": "..."}`
- `process_withdrawal(db_path, customer_id, amount)` → `{"ok": True, "balance": ...}` or `{"ok": False, "error": "..."}`
- Validation rules enforced in services (positive number, finite, sufficient balance)

**Todo List:**
1. Write `BACKEND/services.py` with all four service functions
2. Use `math.isfinite` to reject infinity/NaN in deposit and withdrawal
3. Return uniform dict results — never raise exceptions to the caller

**Status:** [ ] pending

---

## Sub-Task 4 — Flask App Entry Point & Routes (`app.py`, `routes.py`)

**Intent:** Wire the HTTP layer together. `app.py` configures and starts the app; `routes.py` maps URLs to service calls and serves HTML pages.

**Expected Outcomes:**
- `BACKEND/app.py`: creates Flask app, sets `SECRET_KEY`, sets `DATABASE` config key to absolute path of `banking.db`, imports routes, calls `init_db` at startup, runs on port 5000 with `debug=True`
- `BACKEND/routes.py`: 7 routes as specified in the guide
  - `GET /` → redirect to `/login`
  - `GET /login` → serve `FRONTEND/login.html`
  - `POST /login` → authenticate, set session, return JSON
  - `GET /logout` → clear session, redirect to `/login`
  - `GET /dashboard` → session guard, serve `FRONTEND/dashboard.html`
  - `GET /balance` → session guard, return JSON balance
  - `POST /deposit` → session guard, call deposit service, return JSON
  - `POST /withdraw` → session guard, call withdrawal service, return JSON
- HTML files served via `send_from_directory` pointing at the `FRONTEND/` folder
- All JSON error responses use shape `{"error": "message"}` with appropriate HTTP status codes
- Session stores `user_id` and `username` on login

**Todo List:**
1. Write `BACKEND/app.py`
2. Write `BACKEND/routes.py` with all 8 routes
3. Confirm `send_from_directory` path resolves correctly relative to `BACKEND/`

**Status:** [ ] pending

---

## Sub-Task 5 — Frontend Pages

**Intent:** Build all four HTML pages. Each is a self-contained Bootstrap 5 page that communicates with Flask via `fetch`.

**Expected Outcomes:**
- `FRONTEND/login.html` — login form, error display, posts to `/login`, redirects to `/dashboard` on success
- `FRONTEND/dashboard.html` — greeting with username from `sessionStorage`, balance fetched from `/balance` on load, navigation to deposit/withdraw, logout link
- `FRONTEND/deposit.html` — amount form, client-side validation, posts to `/deposit`, shows new balance or error
- `FRONTEND/withdraw.html` — amount form, client-side validation, posts to `/withdraw`, shows new balance or error
- `FRONTEND/static/styles.css` — minimal custom CSS (bank colour accent, card shadow)
- All pages use Bootstrap 5 CDN, are responsive, have consistent nav header

**Todo List:**
1. Write `FRONTEND/login.html`
2. Write `FRONTEND/dashboard.html`
3. Write `FRONTEND/deposit.html`
4. Write `FRONTEND/withdraw.html`
5. Write `FRONTEND/static/styles.css`

**Status:** [ ] pending

---

## Sub-Task 6 — Unit Tests

**Intent:** Verify all service functions and model helpers work correctly in isolation using an in-memory SQLite database.

**Expected Outcomes:**
- `tests/unit/test_services.py` covers: valid login, wrong password, unknown user, positive deposit, zero deposit, negative deposit, valid withdrawal, withdrawal equal to balance, withdrawal exceeding balance, zero withdrawal
- `tests/unit/test_models.py` covers: `get_customer_by_username` found/not-found, `get_balance`, `update_balance`
- All tests use a pytest fixture that creates a fresh in-memory DB (`:memory:`) and tears it down after each test
- All unit tests pass with `pytest tests/unit/`

**Todo List:**
1. Write `tests/unit/conftest.py` with shared `db_path` fixture (temp file, not `:memory:`, so path can be passed as string)
2. Write `tests/unit/test_models.py`
3. Write `tests/unit/test_services.py`

**Status:** [ ] pending

---

## Sub-Task 7 — Integration Tests

**Intent:** Test the full HTTP stack using Flask's test client — routes, session management, JSON responses, and HTTP status codes.

**Expected Outcomes:**
- `tests/integration/test_routes.py` covers all 9 scenarios from the implementation guide
- Fixture creates a Flask test app pointed at a temporary test database
- After each test the database file is deleted
- All integration tests pass with `pytest tests/integration/`

**Todo List:**
1. Write `tests/integration/conftest.py` with `app` and `client` fixtures
2. Write `tests/integration/test_routes.py` with all route test cases

**Status:** [ ] pending

---

## Sub-Task 8 — Final Validation & README

**Intent:** Confirm everything runs end-to-end and provide a single-file startup guide.

**Expected Outcomes:**
- `pytest` run from project root passes with 0 failures
- `python app.py` starts without errors, `banking.db` is created, app reachable at `http://127.0.0.1:5000`
- `README.md` at project root with: quick-start steps, demo credentials, project structure overview

**Todo List:**
1. Write `README.md`
2. Confirm all files are in their correct locations per the folder structure in `IMPLEMENTATION_PLAN.md`

**Status:** [ ] pending
