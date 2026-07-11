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

- A small, fixed set of customer accounts is seeded into the database at startup.
- SQLite is acceptable for the demo; no concurrent write load is expected.
- Bootstrap is loaded from a CDN; no build toolchain is needed.
- Python 3.11 is the runtime target, consistent with the CI/CD pipeline.
