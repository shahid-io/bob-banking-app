"""
tests/unit/test_models.py

Unit tests for the models layer.  Each test receives a fresh seeded database
via the db_path fixture defined in conftest.py.
"""

from models import get_customer_by_username, get_balance, update_balance


class TestGetCustomerByUsername:
    def test_existing_user_returned(self, db_path):
        cust = get_customer_by_username(db_path, "alice")
        assert cust is not None
        assert cust["username"] == "alice"
        assert cust["full_name"] == "Alice Johnson"

    def test_all_required_fields_present(self, db_path):
        cust = get_customer_by_username(db_path, "bob")
        for field in ("id", "full_name", "username", "password_hash", "balance"):
            assert field in cust, f"Missing field: {field}"

    def test_unknown_username_returns_none(self, db_path):
        assert get_customer_by_username(db_path, "nobody") is None

    def test_case_sensitive_username(self, db_path):
        # Usernames are stored lowercase; 'Alice' should not match 'alice'
        assert get_customer_by_username(db_path, "Alice") is None


class TestGetBalance:
    def test_returns_seeded_balance(self, db_path):
        cust = get_customer_by_username(db_path, "alice")
        bal = get_balance(db_path, cust["id"])
        assert bal == 1000.00

    def test_different_accounts_have_different_balances(self, db_path):
        alice_id = get_customer_by_username(db_path, "alice")["id"]
        carol_id = get_customer_by_username(db_path, "carol")["id"]
        assert get_balance(db_path, alice_id) != get_balance(db_path, carol_id)

    def test_unknown_id_returns_none(self, db_path):
        assert get_balance(db_path, 99999) is None


class TestUpdateBalance:
    def test_balance_is_updated(self, db_path):
        cust = get_customer_by_username(db_path, "alice")
        cid = cust["id"]
        update_balance(db_path, cid, 555.50)
        assert get_balance(db_path, cid) == 555.50

    def test_balance_can_be_set_to_zero(self, db_path):
        cust = get_customer_by_username(db_path, "alice")
        cid = cust["id"]
        update_balance(db_path, cid, 0.0)
        assert get_balance(db_path, cid) == 0.0

    def test_update_does_not_affect_other_accounts(self, db_path):
        alice_id = get_customer_by_username(db_path, "alice")["id"]
        bob_id   = get_customer_by_username(db_path, "bob")["id"]
        bob_bal_before = get_balance(db_path, bob_id)
        update_balance(db_path, alice_id, 9999.00)
        assert get_balance(db_path, bob_id) == bob_bal_before
