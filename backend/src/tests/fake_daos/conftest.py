from unittest.mock import MagicMock

import pytest
from app.main import app
from app.models import UserDAO
from fastapi.testclient import TestClient

from .fake_models import FakeTodoDAO, FakeUserDAO


@pytest.fixture
def client():
    "Fixture to return an HTTP client for the fastapi app"
    yield TestClient(app=app)


@pytest.fixture
async def db_session():
    """
    Fixture for a database session when using FakeDAO classes.
    Patch this into files that use the syntax,
    async with db_session as session:
        ...

    This will handle resetting the FakeDAO CACHE dictionaries
    after each test.
    """
    mock_session = MagicMock()
    yield mock_session
    for fake_dao in [FakeUserDAO, FakeTodoDAO]:
        fake_dao.CACHE = {}


@pytest.fixture
async def fake_user(db_session: MagicMock):
    "Fixture for creating a seed test user"
    user_data = {"name": "test_user", "password": "pass"}
    user = await FakeUserDAO.create(db_session, user_data)
    yield user


@pytest.fixture
def authed_client(client: TestClient, fake_user: UserDAO):
    """
    Fixture to create an HTTP client that includes
    the Authorization header to authenticate against
    FastAPI endpoints, using the "test_user" credentials
    """
    auth_header = {"Authorization": f"bearer {fake_user.name}"}
    client.headers.update(auth_header)
    return client
