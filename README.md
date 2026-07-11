# SecureBank — Banking Web Application

A full-stack banking demo built with **HTML + Bootstrap 5**, **Python 3.11 + Flask**, and **SQLite**.

---

## Quick Start

### Prerequisites

- Python 3.11 or later (`python3 --version`)
- pip (bundled with Python)
- GNU Make (optional — `make` shortcuts listed below)

### 1 — Clone and install

```bash
# From the project root:
make install
# — or manually:
python3 -m venv BACKEND/venv
source BACKEND/venv/bin/activate
pip install -r BACKEND/requirements.txt
```

### 2 — Configure environment (optional)

```bash
cp .env.example .env
# Edit .env — only required in production.
# In development all defaults are already set.
```

### 3 — Run the application

```bash
make run
# — or manually:
cd BACKEND && source venv/bin/activate && python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The SQLite database (`BACKEND/banking.db`) is created automatically with seeded demo accounts on first run.

---

## Demo Credentials

| Username | Password     | Starting Balance |
|----------|--------------|------------------|
| alice    | password123  | $1,000.00        |
| bob      | password456  | $1,500.00        |
| carol    | password789  | $2,000.00        |

---

## Features

| Feature        | Description                                      |
|----------------|--------------------------------------------------|
| Customer Login | Authenticate with username + password            |
| Dashboard      | View current account balance                     |
| Deposit        | Add a positive amount to your account            |
| Withdraw       | Take funds (insufficient-balance check enforced) |
| Logout         | Securely clear your session                      |

---

## Developer Commands (Makefile)

```bash
make install    # Create venv + install all dependencies
make run        # Start Flask development server on port 5000
make test       # Run the full pytest suite (78 tests)
make coverage   # Run tests and print coverage report
make lint       # Lint with ruff
make format     # Auto-format with ruff + black
make clean      # Remove __pycache__, coverage artefacts, banking.db
make help       # Print all targets
```

---

## Running Tests

```bash
make test
# — or manually:
cd BACKEND && source venv/bin/activate
python3 -m pytest ../tests/ -v
```

Expected: **78 passed** (33 unit + 34 integration + 11 security)

### Coverage

```bash
make coverage
# Expected: >= 94% overall
```

---

## Project Structure

```
bob-banking-app/
│
├── FRONTEND/                        # Static HTML pages (Bootstrap 5 CDN)
│   ├── login.html
│   ├── dashboard.html
│   ├── deposit.html
│   ├── withdraw.html
│   └── static/
│       └── styles.css
│
├── BACKEND/                         # Python Flask application
│   ├── app.py                       # create_app() factory + entry point
│   ├── config.py                    # BaseConfig / Dev / Test / Prod hierarchy
│   ├── routes.py                    # Blueprint, error handlers, security headers
│   ├── models.py                    # SQLite access layer (CHECK constraints + index)
│   ├── services.py                  # Business logic -> ServiceResult dataclass
│   ├── requirements.txt             # Pinned Python dependencies
│   └── banking.db                   # SQLite database (auto-created, git-ignored)
│
├── tests/
│   ├── unit/
│   │   ├── conftest.py              # db_path fixture (fresh temp DB per test)
│   │   ├── test_models.py           # 10 model layer tests
│   │   └── test_services.py         # 23 service layer tests
│   └── integration/
│       ├── conftest.py              # create_app factory + test client fixtures
│       ├── test_routes.py           # 34 HTTP endpoint integration tests
│       └── test_security.py         # 11 security header + error handler tests
│
├── .env.example                     # Environment variable reference (copy to .env)
├── .coveragerc                      # Coverage configuration
├── pyproject.toml                   # Build metadata + pytest + coverage config
├── ruff.toml                        # Linter + formatter configuration
├── Makefile                         # Developer convenience targets
├── IMPLEMENTATION_PLAN.md           # Architecture and planning document
├── STEP_BY_STEP_IMPLEMENTATION_GUIDE.md
└── README.md
```

---

## Architecture

```
Browser (HTML + Bootstrap 5)
        |  HTTP + JSON (fetch API)
        v
Flask Blueprint — banking_bp (routes.py)
        |  @after_request: security headers on every response
        |  session guard on protected routes
        v
Service Layer (services.py) -> ServiceResult dataclass
        |  all validation + business rules live here
        v
Models Layer (models.py)
        |  sqlite3 — CHECK constraints + index on username
        v
SQLite Database (BACKEND/banking.db)
```

### API Endpoints

| Method | Endpoint     | Auth | Description                           |
|--------|--------------|------|---------------------------------------|
| GET    | `/`          | No   | Redirects to `/login`                 |
| GET    | `/login`     | No   | Login page                            |
| POST   | `/login`     | No   | Authenticate; creates session         |
| GET    | `/logout`    | Yes  | Clears session; redirects to login    |
| GET    | `/dashboard` | Yes  | Dashboard page                        |
| GET    | `/balance`   | Yes  | `{"balance": float, "username": str}` |
| GET    | `/deposit`   | Yes  | Deposit page                          |
| POST   | `/deposit`   | Yes  | Add funds -> `{"balance": float}`     |
| GET    | `/withdraw`  | Yes  | Withdraw page                         |
| POST   | `/withdraw`  | Yes  | Subtract funds -> `{"balance": float}`|

---

## Configuration

All configuration is managed through `BACKEND/config.py`.

| Class              | Use case                          |
|--------------------|-----------------------------------|
| `DevelopmentConfig`| Local development (`DEBUG=True`)  |
| `TestingConfig`    | pytest / CI (`TESTING=True`)      |
| `ProductionConfig` | Deployed server                   |

The active config is selected by the `FLASK_ENV` environment variable
(`development` | `testing` | `production`).

### Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in values as needed.

| Variable       | Default                                | Required in prod |
|----------------|----------------------------------------|------------------|
| `SECRET_KEY`   | `dev-secret-key-replace-in-production` | Yes              |
| `DATABASE_URL` | `BACKEND/banking.db`                   | Yes              |
| `LOG_LEVEL`    | `INFO`                                 |                  |
| `FLASK_ENV`    | `development`                          |                  |

---

## Security Notes

- Passwords hashed with `werkzeug.security.generate_password_hash` (PBKDF2-SHA256).
- Session cookies: `HttpOnly=True`, `SameSite=Lax`. Set `SESSION_COOKIE_SECURE=True` behind HTTPS.
- Security headers on every response: `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`.
- Login endpoint returns the same error for unknown user and wrong password (prevents enumeration).
- `SECRET_KEY` must be set from an environment variable in production.

---

## Production Checklist

- [ ] Set `SECRET_KEY` from environment — never hardcoded.
- [ ] Set `FLASK_ENV=production`.
- [ ] Serve behind Gunicorn or uWSGI, not Flask's built-in dev server.
- [ ] Serve over HTTPS and set `SESSION_COOKIE_SECURE=True`.
- [ ] Serve static assets from Nginx or a CDN.
- [ ] Replace SQLite with a production database (PostgreSQL, etc.).
- [ ] Enable application-level logging to a file or syslog.

---

## Stopping the Server

Press `Ctrl + C` in the terminal where `python app.py` is running.
