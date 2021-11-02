import pytest
from app.db import db_session
from app.models import User


@pytest.fixture
def fake_userdao():
    pass


def test_unauthenticated(client):
    endpoint = "/me"
    resp = client.get(endpoint)
    assert resp.status_code == 401


def test_login(client, session):
    user = User(name="test_user", password="pass")
    session.add(user)
    session.commit()
    session.flush()
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


def test_failed_login(client):
    pass
