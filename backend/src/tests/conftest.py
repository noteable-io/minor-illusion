from unittest.mock import MagicMock

import pytest
from app.main import app
from app.models import UserDAO
from fastapi.testclient import TestClient

from .fake_models import FakeUserDAO


@pytest.fixture
def client():
    "Fixture to return an HTTP client for the fastapi app"
    yield TestClient(app=app)


@pytest.fixture
async def db_session():
    """
    Fixture to create a mock db_session.
    This should be patched in whenever code uses
    async with db_session() as session:
        ...
    """
    # FakeDAO objects will store models in their CACHE
    # in the form {mock_session: {real_DAO_model.id: real_DAO_model}}
    #
    # However when you call a mock like "session = mock_session()""
    # or enter a context like "async with mock_session() as session:"
    # those return new Mock objects, which means new top level keys
    # in the FakeDAO CACHE.
    #
    # To get around that, we have the return value (db_session())
    # and context manager (async with db_session()) return the same
    # mock_session object
    # e.g.
    # >>> async with mock_session() as session:
    #         print(mock_session)
    #         print(session)
    #
    # <MagicMock id='140405841645728'>
    # <MagicMock id='140405841645728'>
    mock_session = MagicMock()

    def return_same_session(*args, **kwargs):
        return mock_session

    async def areturn_same_session(*args, **kwargs):
        return mock_session

    mock_session.__aenter__ = areturn_same_session
    mock_session.side_effect = return_same_session
    yield mock_session


@pytest.fixture
async def fake_user(db_session: MagicMock):
    "Fixture for creating a seed test user"
    user_data = {"name": "test_user", "password": "pass"}
    user = await FakeUserDAO.create(db_session, user_data)
    yield user
    # deleting the db_session from the CACHE is roughly equivalent
    # to a transactional rollback if we had a real db session
    FakeUserDAO.CACHE.pop(db_session)


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
