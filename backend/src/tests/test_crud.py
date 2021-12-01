import uuid
from unittest.mock import MagicMock

import pytest
from app.models import TodoDAO, UserDAO
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from .fake_models import FakeTodoDAO, FakeUserDAO


@pytest.mark.asyncio
class TestCrud:
    @pytest.fixture(autouse=True)
    def patch_auth_file(self, mocker: MockerFixture, db_session: MagicMock):
        mocker.patch("app.auth.db_session", db_session)
        mocker.patch("app.auth.UserDAO", FakeUserDAO)

    @pytest.fixture(autouse=True)
    def patch_crud_file(self, mocker: MockerFixture, db_session: MagicMock):
        mocker.patch("app.crud.UserDAO", FakeUserDAO)
        mocker.patch("app.crud.TodoDAO", FakeTodoDAO)
        mocker.patch("app.crud.db_session", db_session)

    @pytest.fixture
    async def seed_todos(self, db_session: MagicMock, fake_user: UserDAO):
        # Create some fake seed Todo data for our fake test_user
        todo1 = TodoDAO(id=uuid.UUID(int=1), title="1", content="foo", user=fake_user)
        todo2 = TodoDAO(id=uuid.UUID(int=2), title="2", content="bar", user=fake_user)
        todo3 = TodoDAO(id=uuid.UUID(int=3), title="3", content="baz", user=fake_user)
        await FakeTodoDAO.create(db_session, todo1)
        await FakeTodoDAO.create(db_session, todo2)
        await FakeTodoDAO.create(db_session, todo3)
        yield
        FakeTodoDAO.CACHE.pop(db_session)

    def test_create_todo(self, authed_client: TestClient):
        # User should have no todos to start
        resp = authed_client.get("/todo")
        assert len(resp.json()) == 0

        data = {"title": "test", "content": "test create todo"}
        resp = authed_client.post("/todo/", json=data)
        assert resp.json()["title"] == "test"
        assert resp.json()["content"] == "test create todo"

        # Check that user has exactly one todo now
        resp = authed_client.get("/todo")
        assert len(resp.json()) == 1

    def test_invalid_create_todo(self, authed_client: TestClient):
        data = {"foo": "bar"}
        resp = authed_client.post("/todo/", json=data)
        assert resp.status_code == 422
        assert resp.json() == {
            "detail": [
                {
                    "loc": ["body", "title"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "content"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
            ]
        }

    def test_get_all_todos(self, authed_client: TestClient, seed_todos: None):
        resp = authed_client.get("/todo")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_get_todo_by_id(self, authed_client: TestClient, seed_todos: None):
        resp = authed_client.get(f"/todo/{uuid.UUID(int=1)}")
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "1"
        assert js["content"] == "foo"

    def test_get_todo_by_id_does_not_exist(self, authed_client: TestClient):
        resp = authed_client.get(f"/todo/{uuid.UUID(int=4)}")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Todo not found"}

    def test_update_todo(self, authed_client: TestClient, seed_todos: None):
        endpoint = f"/todo/{uuid.UUID(int=1)}"
        data = {"title": "new title", "content": "new content"}
        # a PUT to /todo/{id} should return the new values
        resp = authed_client.put(endpoint, json=data)
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "new title"
        assert js["content"] == "new content"

        # a GET to /todo/{id} should also have the new values
        resp = authed_client.get(endpoint)
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "new title"
        assert js["content"] == "new content"

    def test_delete_todo(self, authed_client: TestClient, seed_todos: None):
        endpoint = f"/todo/{uuid.UUID(int=1)}"
        resp = authed_client.get(endpoint)
        assert resp.status_code == 200

        # delete the todo
        resp = authed_client.delete(endpoint)
        assert resp.status_code == 200
        assert resp.json() == {}

        # make sure we get 404 if trying to DELETE again
        resp = authed_client.delete(endpoint)
        assert resp.status_code == 404

        # and 404 trying to GET it again
        resp = authed_client.get(endpoint)
        assert resp.status_code == 404
