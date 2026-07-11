"""
tests/unit/test_services.py

Unit tests for the services layer.
Service functions return a ``ServiceResult`` dataclass.
Tests access named attributes: result.ok, result.balance, result.error, etc.
"""

from __future__ import annotations

import math

import pytest

from models import get_customer_by_username
from services import ServiceResult, authenticate, fetch_balance, process_deposit, process_withdrawal


class TestAuthenticate:
    def test_valid_credentials_return_ok(self, db_path):
        result = authenticate(db_path, "alice", "password123")
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert result.name == "Alice Johnson"
        assert result.id is not None

    def test_wrong_password_returns_failure(self, db_path):
        result = authenticate(db_path, "alice", "wrong-password")
        assert result.ok is False
        assert result.error is not None

    def test_unknown_username_returns_failure(self, db_path):
        assert not authenticate(db_path, "nobody", "password123").ok

    def test_error_message_is_generic(self, db_path):
        r1 = authenticate(db_path, "nobody", "x")
        r2 = authenticate(db_path, "alice", "wrong")
        assert r1.error == r2.error

    def test_empty_username_returns_failure(self, db_path):
        assert not authenticate(db_path, "", "password123").ok

    def test_empty_password_returns_failure(self, db_path):
        assert not authenticate(db_path, "alice", "").ok


class TestFetchBalance:
    def test_returns_balance_for_valid_id(self, db_path):
        cust = get_customer_by_username(db_path, "alice")
        result = fetch_balance(db_path, cust["id"])
        assert result.ok is True
        assert result.balance == 1000.00

    def test_unknown_id_returns_failure(self, db_path):
        result = fetch_balance(db_path, 99999)
        assert result.ok is False


class TestProcessDeposit:
    def _cid(self, db_path):
        return get_customer_by_username(db_path, "alice")["id"]

    def test_valid_deposit_increases_balance(self, db_path):
        result = process_deposit(db_path, self._cid(db_path), 250)
        assert result.ok is True
        assert result.balance == 1250.00

    def test_balance_reflects_deposit_amount_exactly(self, db_path):
        cid = self._cid(db_path)
        process_deposit(db_path, cid, 100)
        assert process_deposit(db_path, cid, 50).balance == 1150.00

    def test_zero_amount_rejected(self, db_path):
        assert not process_deposit(db_path, self._cid(db_path), 0).ok

    def test_negative_amount_rejected(self, db_path):
        assert not process_deposit(db_path, self._cid(db_path), -100).ok

    def test_non_numeric_string_rejected(self, db_path):
        assert not process_deposit(db_path, self._cid(db_path), "abc").ok

    def test_infinity_rejected(self, db_path):
        assert not process_deposit(db_path, self._cid(db_path), math.inf).ok

    def test_nan_rejected(self, db_path):
        assert not process_deposit(db_path, self._cid(db_path), math.nan).ok

    def test_float_string_accepted(self, db_path):
        result = process_deposit(db_path, self._cid(db_path), "50.00")
        assert result.ok is True
        assert result.balance == 1050.00


class TestProcessWithdrawal:
    def _cid(self, db_path):
        return get_customer_by_username(db_path, "alice")["id"]

    def test_valid_withdrawal_decreases_balance(self, db_path):
        result = process_withdrawal(db_path, self._cid(db_path), 200)
        assert result.ok is True
        assert result.balance == 800.00

    def test_withdrawal_exact_balance_leaves_zero(self, db_path):
        result = process_withdrawal(db_path, self._cid(db_path), 1000.00)
        assert result.ok is True
        assert result.balance == 0.00

    def test_exceeding_balance_rejected(self, db_path):
        result = process_withdrawal(db_path, self._cid(db_path), 1500)
        assert result.ok is False
        assert result.error == "Insufficient balance"

    def test_zero_amount_rejected(self, db_path):
        assert not process_withdrawal(db_path, self._cid(db_path), 0).ok

    def test_negative_amount_rejected(self, db_path):
        assert not process_withdrawal(db_path, self._cid(db_path), -50).ok

    def test_non_numeric_string_rejected(self, db_path):
        assert not process_withdrawal(db_path, self._cid(db_path), "xyz").ok

    def test_infinity_rejected(self, db_path):
        assert not process_withdrawal(db_path, self._cid(db_path), math.inf).ok
