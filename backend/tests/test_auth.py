"""Tests for /api/auth endpoints."""


class TestRegister:
    def test_registers_successfully(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"username": "alice", "password": "supersecret1"},
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["username"] == "alice"
        assert "id" in body
        # Password must never appear in response
        assert "password" not in body
        assert "password_hash" not in body

    def test_duplicate_username_returns_409(self, client):
        client.post("/api/auth/register", json={"username": "alice", "password": "supersecret1"})
        resp = client.post("/api/auth/register", json={"username": "alice", "password": "supersecret1"})
        assert resp.status_code == 409

    def test_short_password_returns_422(self, client):
        resp = client.post("/api/auth/register", json={"username": "bob", "password": "short"})
        assert resp.status_code == 422

    def test_short_username_returns_422(self, client):
        resp = client.post("/api/auth/register", json={"username": "ab", "password": "validpassword"})
        assert resp.status_code == 422

    def test_invalid_username_chars_returns_422(self, client):
        resp = client.post("/api/auth/register", json={"username": "bad user!", "password": "validpassword"})
        assert resp.status_code == 422

    def test_missing_fields_returns_422(self, client):
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 422

    def test_username_normalised_to_lowercase(self, client):
        resp = client.post("/api/auth/register", json={"username": "ALICE", "password": "supersecret1"})
        assert resp.status_code == 201
        assert resp.get_json()["username"] == "alice"


class TestLogin:
    def _register(self, client, username="testuser", password="testpassword1"):
        client.post("/api/auth/register", json={"username": username, "password": password})

    def test_login_returns_token(self, client):
        self._register(client)
        resp = client.post("/api/auth/login", json={"username": "testuser", "password": "testpassword1"})
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_wrong_password_returns_401(self, client):
        self._register(client)
        resp = client.post("/api/auth/login", json={"username": "testuser", "password": "wrongpassword"})
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "testpassword1"})
        assert resp.status_code == 401

    def test_error_message_does_not_reveal_username(self, client):
        """Both 'wrong user' and 'wrong password' should return the same message."""
        self._register(client)
        resp_bad_pass = client.post("/api/auth/login", json={"username": "testuser", "password": "wrong"})
        resp_bad_user = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
        assert resp_bad_pass.get_json()["error"] == resp_bad_user.get_json()["error"]

    def test_token_grants_access_to_protected_route(self, client):
        self._register(client)
        resp = client.post("/api/auth/login", json={"username": "testuser", "password": "testpassword1"})
        token = resp.get_json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        cats = client.get("/api/categories/", headers=headers)
        assert cats.status_code == 200
