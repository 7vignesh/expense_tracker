"""Tests for the /api/expenses endpoints."""

import pytest


VALID_EXPENSE = {
    "description": "Lunch",
    "amount": "12.50",
    "date": "2026-01-15",
}


class TestCreateExpense:
    def test_creates_successfully(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["description"] == "Lunch"
        assert body["amount"] == "12.50"
        assert body["category"]["name"] == "Food"

    def test_amount_stored_as_exact_decimal(self, client, auth_headers, category):
        """Verify floating-point precision is not lost."""
        resp = client.post(
            "/api/expenses/",
            json={"description": "Item", "amount": "0.01", "date": "2026-01-01", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["amount"] == "0.01"

    def test_future_date_rejected(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "date": "2030-12-31", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_negative_amount_rejected(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "-5.00", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_zero_amount_rejected(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "0.00", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_nonexistent_category_returns_404(self, client, auth_headers):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": 999},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_missing_description_returns_422(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={"amount": "5.00", "date": "2026-01-01", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_too_many_decimal_places_rejected(self, client, auth_headers, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "1.999", "category_id": category["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": category["id"]},
        )
        # category fixture requires auth_headers, but here we send no headers
        assert resp.status_code == 401


class TestListExpenses:
    def _create(self, client, auth_headers, category_id, description, amount, date):
        return client.post(
            "/api/expenses/",
            json={"description": description, "amount": amount, "date": date, "category_id": category_id},
            headers=auth_headers,
        )

    def test_empty_list(self, client, auth_headers):
        resp = client.get("/api/expenses/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_filter_by_category(self, client, auth_headers, category):
        cat_id = category["id"]
        cat2 = client.post("/api/categories/", json={"name": "Transport"}, headers=auth_headers).get_json()

        self._create(client, auth_headers, cat_id, "Lunch", "10.00", "2026-01-01")
        self._create(client, auth_headers, cat2["id"], "Bus", "2.00", "2026-01-01")

        resp = client.get(f"/api/expenses/?category_id={cat_id}", headers=auth_headers)
        results = resp.get_json()
        assert len(results) == 1
        assert results[0]["description"] == "Lunch"

    def test_filter_by_date_range(self, client, auth_headers, category):
        cat_id = category["id"]
        self._create(client, auth_headers, cat_id, "Jan", "10.00", "2026-01-01")
        self._create(client, auth_headers, cat_id, "Feb", "20.00", "2026-02-01")
        self._create(client, auth_headers, cat_id, "Mar", "30.00", "2026-03-01")

        resp = client.get("/api/expenses/?date_from=2026-01-15&date_to=2026-02-28", headers=auth_headers)
        results = resp.get_json()
        assert len(results) == 1
        assert results[0]["description"] == "Feb"

    def test_inverted_date_range_rejected(self, client, auth_headers):
        resp = client.get("/api/expenses/?date_from=2026-12-01&date_to=2026-01-01", headers=auth_headers)
        assert resp.status_code == 400

    def test_user_cannot_see_another_users_expenses(self, client, auth_headers, category):
        """Expenses are scoped to the owning user."""
        cat_id = category["id"]
        self._create(client, auth_headers, cat_id, "My expense", "10.00", "2026-01-01")

        # Register and log in as a second user
        client.post("/api/auth/register", json={"username": "other", "password": "otherpass99"})
        resp2 = client.post("/api/auth/login", json={"username": "other", "password": "otherpass99"})
        other_headers = {"Authorization": f"Bearer {resp2.get_json()['access_token']}"}

        results = client.get("/api/expenses/", headers=other_headers).get_json()
        assert results == []


class TestDeleteExpense:
    def test_deletes_successfully(self, client, auth_headers, category):
        create_resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": category["id"]},
            headers=auth_headers,
        )
        exp_id = create_resp.get_json()["id"]
        resp = client.delete(f"/api/expenses/{exp_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_nonexistent_returns_404(self, client, auth_headers):
        resp = client.delete("/api/expenses/999", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_delete_another_users_expense(self, client, auth_headers, category):
        """Trying to delete someone else's expense returns 403."""
        cat_id = category["id"]
        create_resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": cat_id},
            headers=auth_headers,
        )
        exp_id = create_resp.get_json()["id"]

        client.post("/api/auth/register", json={"username": "other2", "password": "otherpass99"})
        resp2 = client.post("/api/auth/login", json={"username": "other2", "password": "otherpass99"})
        other_headers = {"Authorization": f"Bearer {resp2.get_json()['access_token']}"}

        resp = client.delete(f"/api/expenses/{exp_id}", headers=other_headers)
        assert resp.status_code == 403


class TestSummary:
    def test_empty_summary(self, client, auth_headers):
        resp = client.get("/api/expenses/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total"] == "0.00"
        assert body["by_category"] == {}

    def test_totals_correct(self, client, auth_headers, category):
        cat_id = category["id"]
        client.post("/api/expenses/", json={"description": "A", "amount": "10.50", "date": "2026-01-01", "category_id": cat_id}, headers=auth_headers)
        client.post("/api/expenses/", json={"description": "B", "amount": "4.50", "date": "2026-01-02", "category_id": cat_id}, headers=auth_headers)

        resp = client.get("/api/expenses/summary", headers=auth_headers)
        body = resp.get_json()
        assert body["total"] == "15.00"
        assert body["by_category"]["Food"] == "15.00"
