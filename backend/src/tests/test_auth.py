from unittest.mock import MagicMock, patch

import pytest
from app.models import UserDAO

from .fake_models import FakeUserDAO


class TestAuth:
    @pytest.fixture(autouse=True, scope="class")
    def fake_user(self):
        with patch("app.auth.UserDAO", FakeUserDAO):
            db_session = MagicMock()
            user = UserDAO(name="test_user", password="pass")
            FakeUserDAO.create(db_session, user)
            yield

    def test_unauthenticated(self, client):
        endpoint = "/me"
        resp = client.get(endpoint)
        assert resp.status_code == 401

    def test_login(self, client):
        endpoint = "/auth/login"
        data = {"username": "test_user", "password": "pass"}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 200

        token = resp.json()["access_token"]
        token_type = resp.json()["token_type"]

        auth_header = {"Authorization": f"{token_type} {token}"}
        endpoint = "/me"
        resp = client.get(endpoint, headers=auth_header)
        assert resp.status_code == 200

    def test_failed_login(self, client):
        endpoint = "/auth/login"
        data = {"username": "test_user", "password": "ssap"}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 403
