import uuid
from unittest.mock import MagicMock, patch

import pytest
from app.models import TodoDAO, UserDAO

from .fake_models import FakeTodoDAO, FakeUserDAO


def make_todo(_id: int, title: str, content: str, user: UserDAO):
    "Helper function to simulate writing Todo's to database"
    todo = TodoDAO(id=uuid.UUID(int=_id), title=title, content=content, user=user)
    db_session = MagicMock()
    FakeTodoDAO.create(db_session, todo)
    return todo


class TestCrud:
    @pytest.fixture(autouse=True)
    def patch_todo_dao(self):
        FakeTodoDAO.clear()
        with patch("app.crud.TodoDAO", FakeTodoDAO):
            yield

    @pytest.fixture(autouse=True)
    def patch_user_dao(self):
        # need to patch both crud and auth since auth_client
        # is getting user from app.auth
        with patch("app.crud.UserDAO", FakeUserDAO):
            with patch("app.auth.UserDAO", FakeUserDAO):
                yield

    def test_get_all(self, auth_client, fake_user):
        make_todo(_id=1, title="todo1", content="foo", user=fake_user)
        make_todo(_id=2, title="todo2", content="bar", user=fake_user)

        resp = auth_client.get("/todo")
        assert resp.status_code == 200
        js = resp.json()
        assert js[0]["id"] == "00000000-0000-0000-0000-000000000001"
        assert js[0]["title"] == "todo1"
        assert js[0]["content"] == "foo"

        assert js[1]["id"] == "00000000-0000-0000-0000-000000000002"
        assert js[1]["title"] == "todo2"
        assert js[1]["content"] == "bar"

    def test_get_todo_by_id(self, auth_client, fake_user):
        make_todo(_id=3, title="todo3", content="baz", user=fake_user)
        resp = auth_client.get(f"/todo/{uuid.UUID(int=3)}")
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000003"
        assert js["title"] == "todo3"
        assert js["content"] == "baz"

    def test_get_todo_by_id_does_not_exist(self, auth_client):
        resp = auth_client.get(f"/todo/{uuid.UUID(int=4)}")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Todo not found"}

    def test_create_todo(self, auth_client):
        data = {"title": "todo5", "content": "abc"}
        resp = auth_client.post("/todo/", json=data)
        assert resp.json()["title"] == "todo5"
        assert resp.json()["content"] == "abc"

        _id = resp.json()["id"]
        resp = auth_client.get(f"/todo/{_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "todo5"
        assert resp.json()["content"] == "abc"

    def test_update_todo(self, auth_client, fake_user):
        make_todo(_id=6, title="todo6", content="xyz", user=fake_user)
        endpoint = f"/todo/{uuid.UUID(int=6)}"
        data = {"title": "new title", "content": "new content"}
        resp = auth_client.put(endpoint, json=data)
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000006"
        assert js["title"] == "new title"
        assert js["content"] == "new content"

    def test_delete_todo(self, auth_client, fake_user):
        make_todo(_id=7, title="todo7", content="delete me", user=fake_user)
        # Make sure it exists
        resp = auth_client.get(f"/todo/{uuid.UUID(int=7)}")
        assert resp.status_code == 200

        # delete the todo
        resp = auth_client.delete(f"/todo/{uuid.UUID(int=7)}")
        assert resp.status_code == 200
        assert resp.json() == {}

        # make sure we get 404 if trying to DELETE again
        resp = auth_client.delete(f"/todo/{uuid.UUID(int=7)}")
        assert resp.status_code == 404

        # and 404 trying to GET it again
        resp = auth_client.get(f"/todo/{uuid.UUID(int=7)}")
        assert resp.status_code == 404
