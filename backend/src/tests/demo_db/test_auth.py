from typing import AsyncIterator

import httpx
import pytest
from app.models import UserDAO
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAuth:
    @pytest.fixture(autouse=True)
    def patch_auth_file(
        self, mocker: MockerFixture, db_session: AsyncIterator[AsyncSession]
    ):
        mocker.patch("app.auth.db_session", db_session)

    async def test_unauthenticated(self, client: httpx.AsyncClient):
        endpoint = "/me"
        resp = await client.get(endpoint)
        assert resp.status_code == 401

    async def test_login(self, client: httpx.AsyncClient, fake_user: UserDAO):
        endpoint = "/auth/login"
        data = {"username": fake_user.name, "password": fake_user.password}
        resp = await client.post(endpoint, data=data)
        assert resp.status_code == 200

        token = resp.json()["access_token"]
        token_type = resp.json()["token_type"]

        auth_header = {"Authorization": f"{token_type} {token}"}
        endpoint = "/me"
        resp = await client.get(endpoint, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "test_user"

    async def test_invalid_password(
        self, client: httpx.AsyncClient, fake_user: UserDAO
    ):
        endpoint = "/auth/login"
        data = {"username": fake_user.name, "password": fake_user.password + "invalid"}
        resp = await client.post(endpoint, data=data)
        assert resp.status_code == 403
        assert resp.json() == {"detail": "Incorrect password"}

    async def test_user_does_not_exist(self, client: httpx.AsyncClient):
        endpoint = "/auth/login"
        data = {"username": "missing", "password": "missing"}
        resp = await client.post(endpoint, data=data)
        assert resp.status_code == 401
        assert resp.json() == {"detail": "User not found"}
