"""Tests for the /api/categories endpoints."""

import pytest


class TestListCategories:
    def test_empty_list(self, client, auth_headers):
        resp = client.get("/api/categories/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_created_category(self, client, auth_headers, category):
        resp = client.get("/api/categories/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Food"

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/categories/")
        assert resp.status_code == 401


class TestCreateCategory:
    def test_creates_successfully(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": "Transport"}, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["name"] == "Transport"
        assert "id" in body

    def test_strips_whitespace(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": "  Rent  "}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Rent"

    def test_duplicate_name_returns_409(self, client, auth_headers, category):
        resp = client.post("/api/categories/", json={"name": "Food"}, headers=auth_headers)
        assert resp.status_code == 409

    def test_empty_name_returns_422(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": ""}, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client, auth_headers):
        resp = client.post("/api/categories/", json={}, headers=auth_headers)
        assert resp.status_code == 422

    def test_name_too_long_returns_422(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": "x" * 101}, headers=auth_headers)
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/api/categories/", json={"name": "Food"})
        assert resp.status_code == 401


class TestDeleteCategory:
    def test_deletes_empty_category(self, client, auth_headers, category):
        cat_id = category["id"]
        resp = client.delete(f"/api/categories/{cat_id}", headers=auth_headers)
        assert resp.status_code == 204

        resp2 = client.get("/api/categories/", headers=auth_headers)
        assert resp2.get_json() == []

    def test_cannot_delete_nonexistent(self, client, auth_headers):
        resp = client.delete("/api/categories/999", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_delete_category_with_expenses(self, client, auth_headers, category):
        cat_id = category["id"]
        client.post(
            "/api/expenses/",
            json={
                "description": "Lunch",
                "amount": "10.00",
                "date": "2026-01-01",
                "category_id": cat_id,
            },
            headers=auth_headers,
        )
        resp = client.delete(f"/api/categories/{cat_id}", headers=auth_headers)
        assert resp.status_code == 409
