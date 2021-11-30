from unittest.mock import MagicMock

import pytest
from app.main import app
from app.models import UserDAO
from fastapi.testclient import TestClient

from .fake_models import FakeUserDAO


@pytest.fixture
def client():
    yield TestClient(app=app)


@pytest.fixture
async def db_session():
    return MagicMock()


@pytest.fixture
async def fake_user(db_session):
    FakeUserDAO.clear()
    user = UserDAO(name="test_user", password="pass")
    await FakeUserDAO.create(db_session, user)
    return user


@pytest.fixture
def auth_client(client, fake_user):
    endpoint = "/auth/login"
    data = {"username": fake_user.name, "password": fake_user.password}
    resp = client.post(endpoint, data=data)

    token = resp.json()["access_token"]
    token_type = resp.json()["token_type"]

    auth_header = {"Authorization": f"{token_type} {token}"}
    client.headers.update(auth_header)
    return client
