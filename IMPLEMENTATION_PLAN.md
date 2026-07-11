# Banking Web Application — Implementation Plan

---

## 1. Solution Overview

### Objective

Build a browser-based banking web application that allows customers to log in, view their account balance, deposit funds, withdraw funds, and log out securely. The application is structured as a two-tier system: a static HTML/Bootstrap frontend communicating with a Python Flask backend backed by a SQLite database.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and session management | User registration / self-service sign-up |
| Dashboard with account balance display | Multi-account or joint account management |
| Deposit and withdrawal transactions | Transfers between accounts |
| Secure logout | External payment integrations |
| REST API served by Flask | Admin portal or bank-staff interface |
| SQLite persistence | Production database migration (PostgreSQL, etc.) |

### Users

- **Customer** — the sole user role. A registered banking customer who authenticates and manages their own account.

### Functional Requirements

| # | Requirement |
|---|---|
| FR-1 | A customer can log in with a username and password. |
| FR-2 | An authenticated customer can view their current account balance on the dashboard. |
| FR-3 | An authenticated customer can deposit a positive amount into their account. |
| FR-4 | An authenticated customer can withdraw a positive amount, subject to sufficient balance. |
| FR-5 | An authenticated customer can log out and terminate their session. |
| FR-6 | Unauthenticated users are redirected to the login page. |

### Non-Functional Requirements

| # | Requirement |
|---|---|
| NFR-1 | Session state is maintained server-side; the browser holds only a session cookie. |
| NFR-2 | Passwords are stored hashed, never in plain text. |
| NFR-3 | All API responses use JSON with consistent status codes. |
| NFR-4 | The frontend is responsive and renders correctly on standard desktop browsers. |
| NFR-5 | The application must be runnable locally with a single `python app.py` command. |
| NFR-6 | The codebase must be structured to support automated testing via pytest. |

### Assumptions

- A small, fixed set of customer accounts is seeded into the database at startup (no registration flow required for the demo scope).
- SQLite is acceptable for the demo; no concurrent write load is expected.
- Bootstrap is loaded from a CDN; no build toolchain (Webpack, Vite, etc.) is needed.
- Python 3.11 is the runtime target, consistent with the CI/CD pipeline.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                        BROWSER                          │
│                                                         │
│   ┌──────────────┐   ┌───────────┐   ┌──────────────┐  │
│   │  login.html  │   │dashboard  │   │deposit /     │  │
│   │              │──▶│  .html    │──▶│withdraw.html │  │
│   └──────────────┘   └───────────┘   └──────────────┘  │
│          HTML + Bootstrap (FRONTEND/)                   │
└────────────────────┬──────────────────────────────────────────┘
                     │  HTTP / JSON (REST)
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   FLASK APPLICATION                     │
│                    (BACKEND/)                           │
│                                                         │
│   ┌────────────┐  ┌───────────────┐  ┌──────────────┐  │
│   │   Auth     │  │  Transaction  │  │  Account     │  │
│   │  Routes    │  │   Routes      │  │  Routes      │  │
│   └─────┬──────┘  └──────┬────────┘  └──────┬───────┘  │
│         └─────────────────────────┘          │
│                          │                              │
│                    ┌─────▼──────┐                       │
│                    │  Services  │                       │
│                    │  / Models  │                       │
│                    └─────┬──────┘                       │
└──────────────────────────┬──────────────────────────────┘
                           │  SQLite (file I/O)
                           ↓
┌─────────────────────────────────────────────────────────┐
│              SQLite DATABASE (banking.db)               │
│                    (BACKEND/)                           │
└─────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

1. The browser loads a static HTML page from the `FRONTEND/` folder.
2. User actions (login, deposit, withdraw) trigger form submissions or JavaScript `fetch` calls to Flask REST endpoints.
3. Flask validates the request, applies business rules, and reads/writes the SQLite database via SQLAlchemy or direct `sqlite3` module calls.
4. Flask returns a JSON response (or a redirect for page navigation).
5. The frontend updates the displayed state accordingly.

### Request Lifecycle

```
Browser Action
     │
     ↓
HTTP Request  ──▶  Flask Route Handler
                        │
                        ↓
                   Session Check  ──(fail)──▶  401 / Redirect to Login
                        │ (pass)
                        ↓
                   Service Layer  (business logic / validation)
                        │
                        ↓
                   Database Query / Write
                        │
                        ↓
                   JSON Response / Redirect
                        │
                        ↓
               Browser renders updated page
```

---

## 3. Component Design

### Frontend Responsibilities (`FRONTEND/`)

- Render all user-facing pages: Login, Dashboard, Deposit, Withdraw.
- Apply Bootstrap layout and styling for a responsive, consistent UI.
- Submit forms or issue `fetch` requests to Flask API endpoints.
- Display success and error feedback returned by the API.
- Enforce basic client-side input validation (non-empty fields, positive numeric amounts) before sending requests.

### Backend Responsibilities (`BACKEND/`)

- Expose REST endpoints for authentication (`/login`, `/logout`) and account operations (`/balance`, `/deposit`, `/withdraw`).
- Manage server-side session state (Flask `session` with a secret key).
- Enforce authentication on protected routes.
- Validate incoming data (correct types, positive amounts, sufficient balance).
- Hash and verify passwords.
- Translate service results into consistent HTTP responses.

### Database Responsibilities (SQLite / `banking.db`)

- Persist customer account records (identity and credentials).
- Persist account balances and maintain data integrity across transactions.
- Provide a seed dataset for demo use (pre-loaded customer accounts).

---

## 4. Folder Structure

```
Banking-application-Bob-demo/
│
├── FRONTEND/                    # All browser-facing static files
│   ├── login.html               # Login page
│   ├── dashboard.html           # Account dashboard (balance display)
│   ├── deposit.html             # Deposit form
│   ├── withdraw.html            # Withdrawal form
│   └── static/
│       └── styles.css           # Custom CSS (supplements Bootstrap CDN)
│
├── BACKEND/                     # Python Flask application
│   ├── app.py                   # Application entry point; Flask app factory
│   ├── routes.py                # All route/endpoint definitions
│   ├── models.py                # Data models and DB access layer
│   ├── services.py              # Business logic (auth, transactions)
│   ├── banking.db               # SQLite database file (auto-created at startup)
│   └── requirements.txt         # Python dependencies
│
├── tests/                       # Automated test suite
│   ├── unit/                    # Unit tests for services and models
│   └── integration/             # Integration tests for API endpoints
│
├── .github/
│   └── workflows/
│       └── banking-app-ci.yml   # GitHub Actions CI pipeline
│
└── docs/
    └── demo-setup/              # Lab guides and setup references
```

### Folder Responsibilities

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/` | Static HTML pages and assets served to the browser |
| `FRONTEND/static/` | CSS overrides and any local static assets |
| `BACKEND/app.py` | Flask app creation, configuration, and startup |
| `BACKEND/routes.py` | URL routing and request/response handling |
| `BACKEND/models.py` | Database models and query helpers |
| `BACKEND/services.py` | Business rules isolated from HTTP layer |
| `BACKEND/banking.db` | SQLite persistent storage |
| `tests/` | pytest-compatible test suite |
| `.github/workflows/` | CI pipeline definitions |
| `docs/demo-setup/` | Reference documentation and lab instructions |

---

## 5. Module Breakdown

### Authentication Module

- **Scope:** Login page, session creation, session validation, logout.
- **Frontend:** `login.html` form submits credentials via POST.
- **Backend:** `/login` POST route validates credentials, creates session; `/logout` route clears session.
- **Key behaviour:** All non-login routes check for an active session and redirect to login if absent.

### Dashboard Module

- **Scope:** Authenticated landing page showing account holder name and current balance.
- **Frontend:** `dashboard.html` fetches balance data on page load and renders it.
- **Backend:** `/balance` GET route returns the authenticated customer's current balance as JSON.
- **Key behaviour:** Serves as the post-login entry point; all navigation links originate here.

### Account Management Module

- **Scope:** Viewing and maintaining the accuracy of a customer's account record.
- **Backend:** Models and service helpers that retrieve and update account records.
- **Key behaviour:** Single source of truth for balance reads; all mutations go through the service layer.

### Transactions Module

- **Scope:** Deposit and withdrawal operations.
- **Frontend:** `deposit.html` and `withdraw.html` forms with amount input.
- **Backend:** `/deposit` POST and `/withdraw` POST routes delegate to the service layer.
- **Key behaviour:** Deposit adds to balance; withdrawal deducts from balance with a check that the result is not negative. Both operations persist atomically to the database.

---

## 6. Implementation Roadmap

### Development Phases

| Phase | Description | Deliverables | Dependencies |
|---|---|---|---|
| **Phase 1 — Foundation** | Project scaffolding, folder creation, Flask app skeleton, SQLite initialisation with seed data. | Runnable `python app.py` with empty routes, `banking.db` created on startup. | None |
| **Phase 2 — Authentication** | Login and logout endpoints, password hashing, session management, login page. | Working login/logout flow; protected routes redirect unauthenticated users. | Phase 1 |
| **Phase 3 — Dashboard & Balance** | Balance endpoint, dashboard page rendering customer name and balance. | Authenticated user sees correct balance on dashboard. | Phase 2 |
| **Phase 4 — Transactions** | Deposit and withdrawal endpoints and pages, balance validation. | Customer can deposit and withdraw; balance updates correctly; insufficient-funds error handled. | Phase 3 |
| **Phase 5 — Polish & Integration** | Consistent error messages, Bootstrap styling, navigation links, end-to-end manual smoke test. | Complete, visually consistent UI; all flows work from browser. | Phase 4 |
| **Phase 6 — Testing** | Unit tests for service layer; integration tests for all API endpoints using pytest. | All tests pass; CI pipeline runs green on push. | Phase 5 |
| **Phase 7 — CI/CD & GitHub** | Configure GitHub Actions workflow; push repository to GitHub. | Code hosted on GitHub; CI pipeline triggers automatically on push. | Phase 6 |

### Estimated Effort

| Phase | Relative Effort |
|---|---|
| Phase 1 — Foundation | Low |
| Phase 2 — Authentication | Medium |
| Phase 3 — Dashboard & Balance | Low |
| Phase 4 — Transactions | Medium |
| Phase 5 — Polish & Integration | Low |
| Phase 6 — Testing | Medium |
| Phase 7 — CI/CD & GitHub | Low |

### Dependencies

- Python 3.11 runtime must be available locally.
- `Flask`, `Werkzeug` (for password hashing), and `pytest` must be listed in `requirements.txt` and installed before development.
- Bootstrap is loaded from CDN — an internet connection is required for frontend rendering during development.
- A GitHub account with a Personal Access Token is required before Phase 7.
- GitHub MCP server (Node.js v18+) must be configured in `.bob/mcp.json` before the repository push step.
