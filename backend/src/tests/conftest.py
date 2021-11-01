from contextlib import contextmanager

import pytest
from app.db import db_session, engine
from app.main import app
from app.models import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

TestSession = sessionmaker()


@pytest.fixture
def client():
    yield TestClient(app=app)


@pytest.fixture
def db_connection():
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture
def session(db_connection):
    transaction = db_connection.begin()
    rollback_session = TestSession(bind=db_connection)
    try:
        yield rollback_session
    finally:
        rollback_session.close()
        transaction.rollback()


app.dependency_overrides[db_session] = session
