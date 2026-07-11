# Makefile — Developer convenience targets for the banking demo project
#
# Usage:
#   make install    — create venv and install all dependencies
#   make run        — start the Flask development server
#   make test       — run the full test suite
#   make coverage   — run tests with coverage report
#   make lint       — run ruff linter
#   make format     — auto-format with ruff and black
#   make clean      — remove build artifacts and caches

PYTHON   := python3
VENV     := BACKEND/venv
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff
BLACK    := $(VENV)/bin/black
FLASK    := $(VENV)/bin/python BACKEND/app.py

# Source files linted/formatted (BACKEND Python + tests)
SRC      := BACKEND/app.py BACKEND/config.py BACKEND/models.py \
            BACKEND/routes.py BACKEND/services.py \
            tests/unit tests/integration

.PHONY: install run test coverage lint format clean help

## install: Set up virtual environment and install all dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r BACKEND/requirements.txt --quiet
	@echo "\n✓  Virtual environment ready at $(VENV)"
	@echo "   Activate with: source $(VENV)/bin/activate"

## run: Start the Flask development server (http://127.0.0.1:5000)
run:
	cd BACKEND && $(PYTHON) app.py

## test: Run the full pytest suite
test:
	$(PYTEST) tests/ -v

## coverage: Run tests and print a coverage report
coverage:
	$(PYTEST) tests/ -v \
	    --cov=BACKEND \
	    --cov-config=.coveragerc \
	    --cov-report=term-missing \
	    --cov-report=html:htmlcov

## lint: Check code style with ruff
lint:
	$(RUFF) check $(SRC)

## format: Auto-format with ruff (isort + pyupgrade) then black
format:
	$(RUFF) check --fix $(SRC) && \
	$(BLACK) $(SRC)

## clean: Remove Python caches, coverage artifacts, and the test database
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	find . -name ".coverage" -delete 2>/dev/null; true
	rm -rf htmlcov .pytest_cache BACKEND/banking.db
	@echo "✓  Clean"

## help: Print this help message
help:
	@grep -E '^## ' Makefile | sed 's/## /  /'
