import pytest

from .fake_models import FakeUserDAO


class TestAuth:
    @pytest.fixture(autouse=True)
    def patch_auth_file(self, mocker, db_session):
        mocker.patch("app.auth.db_session", db_session)
        mocker.patch("app.auth.UserDAO", FakeUserDAO)

    def test_unauthenticated(self, client):
        endpoint = "/me"
        resp = client.get(endpoint)
        assert resp.status_code == 401

    def test_login(self, client, fake_user):
        endpoint = "/auth/login"
        data = {"username": fake_user.name, "password": fake_user.password}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 200

        token = resp.json()["access_token"]
        token_type = resp.json()["token_type"]

        auth_header = {"Authorization": f"{token_type} {token}"}
        endpoint = "/me"
        resp = client.get(endpoint, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "test_user"

    def test_invalid_password(self, client, fake_user):
        endpoint = "/auth/login"
        data = {"username": "test_user", "password": "ssap"}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 403
        assert resp.json() == {"detail": "Incorrect password"}

    def test_user_does_not_exist(self, client):
        endpoint = "/auth/login"
        data = {"username": "missing", "password": "missing"}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 401
        assert resp.json() == {"detail": "User not found"}
