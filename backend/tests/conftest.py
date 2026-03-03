"""
Shared pytest fixtures.

Using an in-memory SQLite DB per test session keeps tests fast and isolated.
Each test that mutates data uses the `client` fixture which wraps everything
in a fresh app context.
"""

import pytest
from app import create_app, db as _db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create a test application once per session."""
    flask_app = create_app(config_override=TestingConfig)
    yield flask_app


@pytest.fixture(scope="function")
def db(app):
    """
    Provide a clean database for every test function.
    Tables are created, test runs, then everything is dropped.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """HTTP test client with a fresh DB."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register a test user, log in, and return bearer headers."""
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpassword123"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def category(client, auth_headers):
    """Create a seeded category and return its JSON payload."""
    resp = client.post(
        "/api/categories/",
        json={"name": "Food"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.get_json()
