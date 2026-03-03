"""Tests for the /api/expenses endpoints."""

import pytest


VALID_EXPENSE = {
    "description": "Lunch",
    "amount": "12.50",
    "date": "2026-01-15",
}


class TestCreateExpense:
    def test_creates_successfully(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": category["id"]},
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["description"] == "Lunch"
        assert body["amount"] == "12.50"
        assert body["category"]["name"] == "Food"

    def test_amount_stored_as_exact_decimal(self, client, category):
        """Verify floating-point precision is not lost."""
        resp = client.post(
            "/api/expenses/",
            json={"description": "Item", "amount": "0.01", "date": "2026-01-01", "category_id": category["id"]},
        )
        assert resp.status_code == 201
        assert resp.get_json()["amount"] == "0.01"

    def test_future_date_rejected(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "date": "2030-12-31", "category_id": category["id"]},
        )
        assert resp.status_code == 422

    def test_negative_amount_rejected(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "-5.00", "category_id": category["id"]},
        )
        assert resp.status_code == 422

    def test_zero_amount_rejected(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "0.00", "category_id": category["id"]},
        )
        assert resp.status_code == 422

    def test_nonexistent_category_returns_404(self, client):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": 999},
        )
        assert resp.status_code == 404

    def test_missing_description_returns_422(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={"amount": "5.00", "date": "2026-01-01", "category_id": category["id"]},
        )
        assert resp.status_code == 422

    def test_too_many_decimal_places_rejected(self, client, category):
        resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "amount": "1.999", "category_id": category["id"]},
        )
        assert resp.status_code == 422


class TestListExpenses:
    def _create(self, client, category_id, description, amount, date):
        return client.post(
            "/api/expenses/",
            json={"description": description, "amount": amount, "date": date, "category_id": category_id},
        )

    def test_empty_list(self, client):
        resp = client.get("/api/expenses/")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_filter_by_category(self, client, category):
        cat_id = category["id"]
        # Create second category
        cat2 = client.post("/api/categories/", json={"name": "Transport"}).get_json()

        self._create(client, cat_id, "Lunch", "10.00", "2026-01-01")
        self._create(client, cat2["id"], "Bus", "2.00", "2026-01-01")

        resp = client.get(f"/api/expenses/?category_id={cat_id}")
        results = resp.get_json()
        assert len(results) == 1
        assert results[0]["description"] == "Lunch"

    def test_filter_by_date_range(self, client, category):
        cat_id = category["id"]
        self._create(client, cat_id, "Jan", "10.00", "2026-01-01")
        self._create(client, cat_id, "Feb", "20.00", "2026-02-01")
        self._create(client, cat_id, "Mar", "30.00", "2026-03-01")

        resp = client.get("/api/expenses/?date_from=2026-01-15&date_to=2026-02-28")
        results = resp.get_json()
        assert len(results) == 1
        assert results[0]["description"] == "Feb"

    def test_inverted_date_range_rejected(self, client):
        resp = client.get("/api/expenses/?date_from=2026-12-01&date_to=2026-01-01")
        assert resp.status_code == 400


class TestDeleteExpense:
    def test_deletes_successfully(self, client, category):
        create_resp = client.post(
            "/api/expenses/",
            json={**VALID_EXPENSE, "category_id": category["id"]},
        )
        exp_id = create_resp.get_json()["id"]
        resp = client.delete(f"/api/expenses/{exp_id}")
        assert resp.status_code == 204

    def test_nonexistent_returns_404(self, client):
        resp = client.delete("/api/expenses/999")
        assert resp.status_code == 404


class TestSummary:
    def test_empty_summary(self, client):
        resp = client.get("/api/expenses/summary")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total"] == "0.00"
        assert body["by_category"] == {}

    def test_totals_correct(self, client, category):
        cat_id = category["id"]
        client.post("/api/expenses/", json={"description": "A", "amount": "10.50", "date": "2026-01-01", "category_id": cat_id})
        client.post("/api/expenses/", json={"description": "B", "amount": "4.50", "date": "2026-01-02", "category_id": cat_id})

        resp = client.get("/api/expenses/summary")
        body = resp.get_json()
        assert body["total"] == "15.00"
        assert body["by_category"]["Food"] == "15.00"
