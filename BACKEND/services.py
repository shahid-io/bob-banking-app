"""
services.py — Business logic layer.

All public functions return a ``ServiceResult`` dataclass instead of a plain
dict.  This gives callers named attributes (``result.ok``, ``result.balance``)
and allows IDEs and type-checkers to verify correctness.

Routes never call models directly; they always go through this layer.
No exceptions are propagated to callers — errors are captured and returned
inside the ``ServiceResult``.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from werkzeug.security import check_password_hash

from models import get_balance, get_customer_by_username, update_balance

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

_GENERIC_AUTH_ERROR = "Invalid username or password"


@dataclass(frozen=True)
class ServiceResult:
    """
    Uniform return type for every service function.

    Attributes:
        ok:      True on success, False on any failure.
        balance: Updated balance (transaction services only).
        id:      Customer database ID (authenticate only).
        name:    Customer display name (authenticate only).
        error:   Human-readable failure message (populated when ok=False).
    """

    ok: bool
    balance: Optional[float] = field(default=None)
    id: Optional[int] = field(default=None)
    name: Optional[str] = field(default=None)
    error: Optional[str] = field(default=None)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def success(
        cls,
        *,
        balance: Optional[float] = None,
        id: Optional[int] = None,  # noqa: A002
        name: Optional[str] = None,
    ) -> "ServiceResult":
        return cls(ok=True, balance=balance, id=id, name=name)

    @classmethod
    def failure(cls, error: str) -> "ServiceResult":
        return cls(ok=False, error=error)


# ---------------------------------------------------------------------------
# Shared amount validation helper
# ---------------------------------------------------------------------------


def _validate_amount(raw: object) -> tuple[Optional[float], Optional[str]]:
    """
    Coerce *raw* to a positive finite float.

    Returns:
        (amount, None)   on success.
        (None, error_msg) on failure.
    """
    try:
        amount = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None, "Invalid amount"

    if not math.isfinite(amount):
        return None, "Invalid amount"

    if amount <= 0:
        return None, "Amount must be greater than zero"

    return amount, None


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def authenticate(db_path: str, username: str, password: str) -> ServiceResult:
    """
    Verify *username* and *password* against the database.

    Returns a ServiceResult with ``id`` and ``name`` on success.
    The same error message is returned for unknown username *and* wrong
    password to prevent username enumeration attacks.
    """
    logger.debug("authenticate: username=%s", username)

    if not username or not password:
        return ServiceResult.failure(_GENERIC_AUTH_ERROR)

    customer = get_customer_by_username(db_path, username)
    if customer is None:
        logger.info("authenticate: unknown username=%s", username)
        return ServiceResult.failure(_GENERIC_AUTH_ERROR)

    if not check_password_hash(str(customer["password_hash"]), password):
        logger.info("authenticate: wrong password for username=%s", username)
        return ServiceResult.failure(_GENERIC_AUTH_ERROR)

    logger.info("authenticate: success for username=%s", username)
    return ServiceResult.success(id=int(str(customer["id"])), name=str(customer["full_name"]))


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


def fetch_balance(db_path: str, customer_id: int) -> ServiceResult:
    """Return the current balance for *customer_id*."""
    balance = get_balance(db_path, customer_id)
    if balance is None:
        return ServiceResult.failure("Account not found")
    return ServiceResult.success(balance=balance)


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------


def process_deposit(db_path: str, customer_id: int, amount: object) -> ServiceResult:
    """
    Add *amount* to the balance of *customer_id*.

    Server-side validation (see STEP_BY_STEP_IMPLEMENTATION_GUIDE.md §5.3):
      - amount must coerce to a finite float
      - amount must be > 0
    """
    validated, error = _validate_amount(amount)
    if error:
        return ServiceResult.failure(error)
    # validated is guaranteed non-None here (error is None when validated is set)
    assert validated is not None

    current = get_balance(db_path, customer_id)
    if current is None:
        return ServiceResult.failure("Account not found")

    new_balance = round(current + validated, 2)
    update_balance(db_path, customer_id, new_balance)
    logger.info(
        "process_deposit: customer_id=%s amount=%.2f new_balance=%.2f",
        customer_id, validated, new_balance,
    )
    return ServiceResult.success(balance=new_balance)


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------


def process_withdrawal(
    db_path: str, customer_id: int, amount: object
) -> ServiceResult:
    """
    Subtract *amount* from the balance of *customer_id*.

    All deposit validation rules apply, plus:
      - resulting balance must not be negative (checked AFTER reading from DB
        to prevent race conditions on cached values)
    """
    validated, error = _validate_amount(amount)
    if error:
        return ServiceResult.failure(error)
    assert validated is not None

    current = get_balance(db_path, customer_id)
    if current is None:
        return ServiceResult.failure("Account not found")

    if validated > current:
        return ServiceResult.failure("Insufficient balance")

    new_balance = round(current - validated, 2)
    update_balance(db_path, customer_id, new_balance)
    logger.info(
        "process_withdrawal: customer_id=%s amount=%.2f new_balance=%.2f",
        customer_id, validated, new_balance,
    )
    return ServiceResult.success(balance=new_balance)
