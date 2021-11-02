from unittest.mock import MagicMock

import pytest
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from .fake_models import FakeTodoDAO, FakeUserDAO


@pytest.fixture
def client():
    yield TestClient(app=app)


@pytest.fixture(autouse=True)
def mock_db_session(mocker):
    mocker.patch("app.db.db_session", MagicMock())


@pytest.fixture(autouse=True)
def mock_daos(mocker):
    mocker.patch("app.models.UserDAO", FakeUserDAO)
    mocker.patch("app.models.TodoDAO", FakeTodoDAO)
