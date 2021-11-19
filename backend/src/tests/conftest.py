from unittest.mock import MagicMock

import pytest
from app.main import app
from fastapi.testclient import TestClient

from .fake_models import FakeUserDAO


@pytest.fixture
def client():
    "Fixture to return an HTTP client for the fastapi app"
    yield TestClient(app=app)


@pytest.fixture
def db_session(mocker):
    """
    Fixture to create a mock db_session.
    This should be patched in whenever code uses
    with db_session() as session:
        ...
    """
    # FakeDAO objects will store models in their CACHE
    # in the form {mock_session: {real_DAO_model.id: real_DAO_model}}
    #
    # However when you call a mock like "session = mock_session()""
    # or enter a context like "with mock_session() as session:"
    # those return new Mock objects, which means new top level keys
    # in the FakeDAO CACHE.
    #
    # To get around that, and ensure there's one session per test
    # make the return value and context block return the same session
    mock_session = MagicMock()

    def return_same_session(*args, **kwargs):
        return mock_session

    mock_session.__enter__ = return_same_session
    mock_session.side_effect = return_same_session
    yield mock_session


@pytest.fixture
def fake_user(db_session):
    "Fixture for creating one user that can be logged in"
    user_data = {"name": "test_user", "password": "pass"}
    user = FakeUserDAO.create(db_session, user_data)
    yield user
    FakeUserDAO.CACHE.pop(db_session)


@pytest.fixture
def authed_client(client, fake_user):
    """
    Fixture to create an HTTP client that includes
    the Authorization header to authenticate against
    FastAPI endpoints, using the "test_user" credentials
    """
    auth_header = {"Authorization": f"bearer {fake_user.name}"}
    client.headers.update(auth_header)
    return client
