from unittest.mock import patch

import pytest

from .fake_models import FakeUserDAO


class TestAuth:
    @pytest.fixture(autouse=True, scope="class")
    def patch_user_dao(self):
        with patch("app.auth.UserDAO", FakeUserDAO):
            yield

    def test_unauthenticated(self, client, fake_user):
        endpoint = "/me"
        resp = client.get(endpoint)
        assert resp.status_code == 401

    def test_login(self, client, fake_user):
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

    def test_failed_login(self, client, fake_user):
        endpoint = "/auth/login"
        data = {"username": "test_user", "password": "ssap"}
        resp = client.post(endpoint, data=data)
        assert resp.status_code == 403
