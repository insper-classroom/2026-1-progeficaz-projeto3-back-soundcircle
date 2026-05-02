"""Testes para o blueprint de autenticação."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "123456",
            "display_name": "Test User",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["message"] == "Usuário criado com sucesso."
        assert data["user"]["email"] == "test@example.com"
        assert any("access_token_cookie" in h for h in resp.headers.getlist("Set-Cookie"))

    def test_register_missing_fields(self, client):
        resp = client.post("/api/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 400
        assert "obrigatórios" in resp.get_json()["error"]

    def test_register_invalid_email(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "invalid",
            "password": "123456",
            "display_name": "User",
        })
        assert resp.status_code == 400
        assert "inválido" in resp.get_json()["error"]

    def test_register_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "a@b.com",
            "password": "123",
            "display_name": "User",
        })
        assert resp.status_code == 400
        assert "6 caracteres" in resp.get_json()["error"]

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "123456",
            "display_name": "User1",
        })
        resp = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "123456",
            "display_name": "User2",
        })
        assert resp.status_code == 409
        assert "E-mail já cadastrado" in resp.get_json()["error"]

    def test_register_duplicate_display_name(self, client):
        client.post("/api/auth/register", json={
            "email": "a@example.com",
            "password": "123456",
            "display_name": "UniqueName",
        })
        resp = client.post("/api/auth/register", json={
            "email": "b@example.com",
            "password": "123456",
            "display_name": "UniqueName",
        })
        assert resp.status_code == 409
        assert "Nome de exibição já está em uso" in resp.get_json()["error"]


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "123456",
            "display_name": "LoginUser",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "123456",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Login realizado com sucesso."
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "wrong@example.com",
            "password": "123456",
            "display_name": "WrongUser",
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401
        assert "incorretos" in resp.get_json()["error"]

    def test_login_user_not_found(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nope@example.com",
            "password": "123456",
        })
        assert resp.status_code == 401
        assert "incorretos" in resp.get_json()["error"]

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 400
        assert "obrigatórios" in resp.get_json()["error"]


class TestMe:
    def test_me_authenticated(self, client):
        client.post("/api/auth/register", json={
            "email": "me@example.com",
            "password": "123456",
            "display_name": "MeUser",
        })
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == "me@example.com"

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["authenticated"] is False


class TestLogout:
    def test_logout_success(self, client):
        client.post("/api/auth/register", json={
            "email": "logout@example.com",
            "password": "123456",
            "display_name": "LogoutUser",
        })
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert "Logout realizado" in resp.get_json()["message"]

    def test_logout_unauthenticated(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401
