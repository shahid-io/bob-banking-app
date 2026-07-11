# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
> This guide provides plain-English instructions explaining *what* to build and *why*, without reproducing full source code.

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing any code, confirm the following tools are available on your machine:

- **Python 3.11** — the runtime for the Flask backend. Verify by running `python --version` or `python3 --version` in your terminal.
- **pip** — Python’s package manager, bundled with Python 3.11.
- **A code editor** — VS Code or any editor with Python support.
- **A modern web browser** — for manual testing of the frontend.

---

### 1.2 Create the Project Folder Structure

Create the two top-level application folders and their sub-directories manually or via terminal:

- `FRONTEND/` — will hold all HTML pages and a `static/` sub-folder for CSS.
- `BACKEND/` — will hold all Python files and the SQLite database.
- `tests/unit/` — for unit tests of services and models.
- `tests/integration/` — for integration tests of API endpoints.

The complete expected layout is documented in Section 4 of the Implementation Plan.

---

### 1.3 Set Up a Python Virtual Environment

A virtual environment isolates this project’s dependencies from other Python projects on the same machine.

- Navigate into the `BACKEND/` folder in your terminal.
- Create a virtual environment using the `venv` module that ships with Python. Give it a name like `venv`.
- **Activate** the virtual environment. On macOS/Linux the activation command sources a shell script inside the `venv/bin/` folder. On Windows it runs a script inside `venv\Scripts\`.
- Once activated, your terminal prompt will change to show the environment name, confirming that any `pip install` commands will install only into this project.

> **Important:** Add `venv/` to your `.gitignore` file so it is never committed to version control.

---

### 1.4 Install Flask and Dependencies

With the virtual environment active, install the required packages using pip:

- **Flask** — the web framework.
- **Werkzeug** — ships with Flask and provides the `generate_password_hash` and `check_password_hash` utilities used for secure password storage.
- **pytest** — the test runner used for unit and integration tests.

After installing, create a `requirements.txt` file inside `BACKEND/` by running `pip freeze > requirements.txt`. This file captures the exact package versions so the environment can be reproduced on any machine (including the CI server) by running `pip install -r requirements.txt`.

---

## 2. Backend Implementation

### 2.1 Create the Flask Application Entry Point (`app.py`)

`app.py` is the single file that starts the application. Its responsibilities are:

1. **Create the Flask app instance** — instantiate `Flask`, passing the name of the module.
2. **Set a secret key** — Flask uses this to sign session cookies. Use a long random string. For the demo, a hardcoded string is fine; in production this would come from an environment variable.
3. **Configure the database path** — store the path to `banking.db` in the app’s configuration dictionary so other modules can read it without hardcoding paths.
4. **Register the routes** — import the routes module and register it with the app (using Flask Blueprints or direct import, depending on your preference).
5. **Initialise the database** — call the database initialisation function (from `models.py`) so that tables are created and demo accounts are seeded the very first time the app runs.
6. **Start the development server** — in the `if __name__ == '__main__':` block, call `app.run()` with `debug=True` so Flask restarts automatically when files change during development.

---

### 2.2 Define Routes (`routes.py`)

Routes are the URL addresses that the browser sends requests to. Define one function per endpoint and decorate it with `@app.route(...)`. The routes needed are:

| Endpoint | HTTP Method | Purpose |
|---|---|---|
| `/login` | GET | Serve the login HTML page |
| `/login` | POST | Accept credentials, validate, create session |
| `/logout` | GET | Clear the session and redirect to login |
| `/dashboard` | GET | Serve the dashboard HTML page |
| `/balance` | GET | Return the current balance as JSON |
| `/deposit` | POST | Accept an amount, add to balance, return result |
| `/withdraw` | POST | Accept an amount, subtract from balance, return result |

**Route logic pattern** — every route that requires a logged-in user should first check whether `user_id` (or similar) is present in Flask’s `session` object. If it is not, the route should immediately return a redirect to `/login`. This is the authentication guard described in FR-6 of the Implementation Plan.

Each route function should do as little work as possible: parse the incoming request data, call the relevant service function, and return the result as a JSON response or an HTML page.

---

### 2.3 Implement the Database and Models Layer (`models.py`)

`models.py` owns everything related to reading and writing the SQLite database. It should contain:

**Database initialisation function:**
- Opens a connection to `banking.db` (SQLite creates the file automatically if it does not exist).
- Creates the necessary tables if they do not already exist. The key tables are one for storing customer account information (including hashed passwords and balance) and one for storing transaction history (optional for the demo scope).
- Seeds two or three demo customer accounts with pre-hashed passwords and starting balances. This seed function should check whether the table is already populated before inserting, so it is safe to call every time the app starts.

**Query helper functions:**
- `get_customer_by_username(username)` — returns the full customer record for a given username, or `None` if not found.
- `get_balance(customer_id)` — returns the current balance for a given customer.
- `update_balance(customer_id, new_balance)` — writes the new balance to the database.

All functions should open their own database connection, perform their operation, commit if writing, and close the connection. This avoids holding open connections longer than necessary.

---

### 2.4 Implement the Service Layer (`services.py`)

Services contain the business logic. They sit between the routes (which handle HTTP) and the models (which handle data storage). This separation keeps each layer focused and testable independently.

**Authentication service:**
- `authenticate(username, password)` — retrieves the customer record by username. If no record is found, return a failure result. If a record is found, use Werkzeug’s `check_password_hash` to compare the submitted password against the stored hash. Return success with the customer’s ID and name if the check passes, or a failure result if it does not.

**Balance service:**
- `fetch_balance(customer_id)` — delegates to the models layer and returns the balance. No logic beyond the delegation is needed here, but having this function means routes never call models directly.

**Deposit service:**
- `process_deposit(customer_id, amount)` — validates that the amount is a positive number (see Section 5 for rules). Reads the current balance, adds the amount, and writes the new balance back via the models layer. Returns the updated balance on success, or an error description on failure.

**Withdrawal service:**
- `process_withdrawal(customer_id, amount)` — validates that the amount is a positive number and that the current balance is sufficient. Reads the current balance, subtracts the amount, and writes the new balance back. Returns the updated balance on success, or an error description on failure.

---

### 2.5 Session Management

Flask’s built-in `session` object works like a dictionary that is stored as a signed cookie in the browser. Use it as follows:

- **On successful login:** Store the customer’s database ID in `session['user_id']` and their display name in `session['username']`. This makes the identity available to every subsequent request without hitting the database again.
- **On logout:** Call `session.clear()` to remove all values from the session, then redirect to `/login`.
- **On protected routes:** Read `session.get('user_id')`. If the value is `None` or absent, the user is not logged in — redirect them immediately.
- **Secret key requirement:** Flask can only sign sessions if `app.secret_key` is set. Without it, any attempt to read or write the session will raise a runtime error.

---

### 2.6 Error Handling

For the demo scope, keep error handling straightforward:

- **Wrong credentials at login:** The authentication service returns a failure result. The route turns this into a JSON response with HTTP status `401 Unauthorized` and a human-readable message such as `"Invalid username or password"`.
- **Validation failures (negative amount, non-numeric input):** The service returns an error description. The route returns HTTP `400 Bad Request` with the message.
- **Insufficient funds on withdrawal:** The service detects the shortfall and returns an error description. The route returns HTTP `422 Unprocessable Entity` with a message like `"Insufficient balance"`.
- **Unauthenticated access to protected routes:** The route redirects to `/login` with HTTP `302`.
- **Unexpected server errors:** Wrap critical sections in try/except blocks. Log the exception details to the console and return HTTP `500 Internal Server Error` with a generic message.

All JSON error responses should use a consistent shape, for example `{ "error": "message text" }`, so the frontend can display them uniformly.

---

## 3. Frontend Implementation

The frontend is entirely static HTML. Each page is a standalone `.html` file inside the `FRONTEND/` folder. Pages communicate with the Flask backend using the browser’s built-in `fetch` API (or standard HTML form `action` attributes pointing to Flask routes).

---

### 3.1 Bootstrap Layout Approach

Every page should share the same structural wrapper:

- A `<head>` section that loads Bootstrap from its CDN using a `<link>` tag and optionally links to `static/styles.css` for minor overrides.
- A centered card or container element (`<div class="container">`, `<div class="card">`) that keeps the UI tidy on wide screens.
- A consistent navigation area (at minimum a logout link) on all authenticated pages.

Bootstrap utility classes (`mt-3`, `btn btn-primary`, `form-control`, `alert alert-danger`, etc.) handle all spacing, colour, and responsive sizing so no custom layout CSS is needed.

---

### 3.2 Login Page (`login.html`)

The login page is the application’s entry point and the only page accessible without a session.

**Structure:**
- A heading identifying the application (e.g. “Banking Portal”).
- A form with two input fields: one for username (type `text`) and one for password (type `password`).
- A submit button labelled “Log In”.
- A hidden `<div>` for displaying error messages (e.g. “Invalid credentials”) that becomes visible when the server returns an error.

**Behaviour:**
- On submit, intercept the form’s default submission with a JavaScript event listener.
- Send the username and password to the `/login` POST endpoint using `fetch` with the body serialised as JSON and the `Content-Type` header set to `application/json`.
- If the response is successful, redirect the browser to `/dashboard` using `window.location.href`.
- If the response is an error, display the error message in the error `<div>`.

---

### 3.3 Dashboard Page (`dashboard.html`)

The dashboard is the first page the customer sees after logging in.

**Structure:**
- A greeting line displaying the customer’s name (e.g. “Welcome, Jane”).
- A prominently styled balance display showing the current account balance.
- Navigation buttons linking to the Deposit and Withdraw pages.
- A Logout button or link.

**Behaviour:**
- Immediately on page load, use `fetch` to call the `/balance` GET endpoint.
- If the response is `401` (session has expired or was never set), redirect to `/login`.
- If the response is successful, extract the balance from the JSON payload and inject it into the DOM.
- The customer name can be embedded in the page by the Flask route when it serves the HTML (as a template variable), or it can be stored in the browser’s `sessionStorage` at login time and read back on page load.

---

### 3.4 Deposit Page (`deposit.html`)

**Structure:**
- A heading “Deposit Funds”.
- A single numeric input labelled “Amount”.
- A submit button labelled “Deposit”.
- A result area that shows the updated balance on success or an error message on failure.
- A back link to the dashboard.

**Behaviour:**
- On submit, validate client-side that the amount field is not empty and contains a positive number (see Section 5).
- Send the amount to the `/deposit` POST endpoint via `fetch`.
- On success, display the new balance returned by the API in the result area.
- On failure, display the error message from the API response.

---

### 3.5 Withdraw Page (`withdraw.html`)

**Structure and behaviour** mirror the Deposit page exactly, with the following differences:

- Heading reads “Withdraw Funds”.
- The form posts to `/withdraw` instead of `/deposit`.
- The error case includes the scenario where the server returns an insufficient-funds message, which should be displayed clearly (e.g. “You do not have enough funds for this withdrawal”).

---

## 4. Integration Steps

### 4.1 Connect the Frontend to the Flask API

The frontend HTML files are static and must be served from somewhere the browser can reach them. For the demo, the simplest approach is:

- Configure Flask to serve the `FRONTEND/` folder as a static file directory, or configure each route to serve the relevant HTML file using Flask’s `send_from_directory` helper.
- All `fetch` calls in the HTML files should use relative URLs (e.g. `/login`, `/balance`) so that the host and port are inherited automatically from wherever Flask is running. This means no URLs need to change between development (`localhost:5000`) and a deployed server.
- Ensure Flask sets the correct CORS headers if the frontend is ever served from a different origin than the backend. For the demo (same origin), no CORS configuration is needed.

---

### 4.2 Connect Flask to SQLite

The connection between Flask and SQLite is managed inside `models.py` using Python’s built-in `sqlite3` module:

- The database file path (`BACKEND/banking.db`) is stored in Flask’s application configuration at startup in `app.py`.
- Each model function reads this path, opens a connection using `sqlite3.connect(db_path)`, performs its query, and closes the connection.
- Use `connection.row_factory = sqlite3.Row` so that query results can be accessed by column name (like a dictionary) rather than by numeric index, which makes the code more readable.
- All write operations (inserts, updates) must call `connection.commit()` before closing, otherwise the change will not be persisted to the file.
- The database initialisation function in `models.py` is called once from `app.py` at startup to ensure the schema and seed data are in place before any request is handled.

---

## 5. Validation Rules

Validation happens at two levels: client-side in the browser (fast feedback, no network round-trip) and server-side in the service layer (authoritative, cannot be bypassed).

### 5.1 Login Validation

| Rule | Where enforced | Response on failure |
|---|---|---|
| Username field must not be empty | Client-side | Inline error message |
| Password field must not be empty | Client-side | Inline error message |
| Username must exist in the database | Server-side (service) | `401` — “Invalid username or password” |
| Password must match the stored hash | Server-side (service) | `401` — “Invalid username or password” |

> **Note:** Always return the same error message regardless of whether it was the username or the password that was wrong. Distinguishing between the two leaks information that aids guessing attacks.

---

### 5.2 Balance Validation

| Rule | Where enforced | Response on failure |
|---|---|---|
| User must be authenticated | Server-side (route guard) | `302` redirect to `/login` |
| Customer ID in session must resolve to a real account | Server-side (model) | `404` — “Account not found” |

---

### 5.3 Deposit Validation

| Rule | Where enforced | Response on failure |
|---|---|---|
| Amount field must not be empty | Client-side | Inline error message |
| Amount must be a valid number | Client-side | Inline error message |
| Amount must be greater than zero | Client-side and server-side | `400` — “Amount must be greater than zero” |
| Amount must be a finite number (no infinity, no NaN) | Server-side | `400` — “Invalid amount” |
| User must be authenticated | Server-side (route guard) | `302` redirect to `/login` |

---

### 5.4 Withdrawal Validation

All deposit rules apply, plus:

| Rule | Where enforced | Response on failure |
|---|---|---|
| Current balance minus amount must be ≥ 0 | Server-side (service) | `422` — “Insufficient balance” |

> The balance check must happen **after** reading the current balance from the database, not against a cached value, to avoid a race condition where two operations read the same balance simultaneously.

---

## 6. Testing

### 6.1 Unit Tests (`tests/unit/`)

Unit tests verify the service layer and model helper functions in isolation, without starting the Flask server or touching the real `banking.db` file.

**What to test in the authentication service:**
- A correct username and correct password returns a success result containing the customer’s ID.
- A correct username with a wrong password returns a failure result.
- A username that does not exist returns a failure result.

**What to test in the deposit service:**
- A positive amount increases the balance by exactly that amount.
- A zero amount is rejected with the appropriate error.
- A negative amount is rejected with the appropriate error.
- A non-numeric string is rejected with the appropriate error.

**What to test in the withdrawal service:**
- A valid amount that is less than the balance decreases the balance correctly.
- An amount equal to the balance reduces the balance to exactly zero (edge case).
- An amount greater than the balance is rejected with an insufficient-funds error.
- Zero and negative amounts are rejected.

**Approach:** Use pytest fixtures to set up a temporary in-memory SQLite database (or a `banking_test.db` file deleted after the test run) so tests do not interfere with each other or with real data.

---

### 6.2 Integration Tests (`tests/integration/`)

Integration tests send real HTTP requests to the Flask application and verify the full stack response including HTTP status codes, response body structure, and database side effects.

**What to test:**

- `POST /login` with valid credentials returns `200` and sets a session cookie.
- `POST /login` with invalid credentials returns `401`.
- `GET /balance` with an active session returns `200` and a numeric balance.
- `GET /balance` without a session returns `401` or a redirect.
- `POST /deposit` with a valid amount returns `200` and the correct new balance.
- `POST /deposit` with a zero or negative amount returns `400`.
- `POST /withdraw` with a valid amount returns `200` and the correct new balance.
- `POST /withdraw` with an amount exceeding the balance returns `422`.
- `GET /logout` clears the session so the next request to `/balance` is rejected.

**Approach:** Use Flask’s built-in test client (`app.test_client()`), which simulates HTTP requests without a network. Create a pytest fixture that initialises a fresh test database before each test and tears it down afterwards to ensure test isolation.

---

### 6.3 Manual Testing Checklist

Run through this checklist in a browser after starting the Flask development server with `python app.py`:

- [ ] Navigating to `http://localhost:5000/dashboard` without logging in redirects to the login page.
- [ ] Submitting the login form with blank username or password shows an inline error before sending any request.
- [ ] Logging in with incorrect credentials shows “Invalid username or password”.
- [ ] Logging in with correct demo credentials lands on the dashboard and displays the correct name and balance.
- [ ] The dashboard balance matches the seeded starting balance for the demo account.
- [ ] Navigating to the Deposit page and submitting a valid amount increases the balance shown on the dashboard.
- [ ] Submitting a deposit of zero or a negative number shows a validation error.
- [ ] Submitting a deposit with no amount shows a validation error.
- [ ] Navigating to the Withdraw page and submitting a valid amount decreases the balance.
- [ ] Submitting a withdrawal amount greater than the current balance shows “Insufficient balance”.
- [ ] Clicking Logout redirects to the login page and clears the session.
- [ ] After logout, attempting to navigate directly to `/dashboard` redirects back to `/login`.
- [ ] All pages render without horizontal scrolling on a standard 1280px wide browser window.

---

## 7. Deployment

### 7.1 Run Locally

To start the application on your local machine:

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment (see Section 1.3).
3. Run `python app.py`.
4. Flask will print the local address it is listening on, typically `http://127.0.0.1:5000`.
5. Open that address in your browser. The application is running.

The SQLite database file (`banking.db`) is created automatically the first time `app.py` runs, so there is no separate database setup step.

To stop the server, press `Ctrl + C` in the terminal.

---

### 7.2 Production Considerations

The development server bundled with Flask is not suitable for production. When moving beyond the demo, the following changes are required:

| Concern | Development approach | Production approach |
|---|---|---|
| Web server | Flask built-in (`app.run()`) | A WSGI server such as Gunicorn or uWSGI |
| Secret key | Hardcoded string in `app.py` | An environment variable injected at deploy time, never committed to source control |
| Database | SQLite file on local disk | A server-grade database (PostgreSQL or MySQL) for concurrent access and durability |
| Debug mode | `debug=True` | `debug=False` — debug mode exposes an interactive console that is a severe security risk if left enabled |
| Static files | Served by Flask | Served by a dedicated web server (Nginx, Apache) or a CDN for performance |
| HTTPS | Not configured | Required — use a TLS certificate (Let’s Encrypt for free certificates) and enforce HTTPS redirects |
| Password policy | Demo accounts seeded at startup | A real registration flow with email verification and strong password requirements |

These are considerations only — implementing them is outside the scope of this demo project.
