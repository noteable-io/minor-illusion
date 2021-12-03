import uuid
from typing import AsyncIterator

import httpx
import pytest
from app.models import TodoDAO, UserDAO
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestCrud:
    @pytest.fixture(autouse=True)
    def patch_auth_file(
        self, mocker: MockerFixture, db_session: AsyncIterator[AsyncSession]
    ):
        mocker.patch("app.auth.db_session", db_session)

    @pytest.fixture(autouse=True)
    def patch_crud_file(
        self, mocker: MockerFixture, db_session: AsyncIterator[AsyncSession]
    ):
        mocker.patch("app.crud.db_session", db_session)

    @pytest.fixture
    async def seed_todos(
        self, db_session: AsyncIterator[AsyncSession], fake_user: UserDAO
    ):
        # Create some fake seed Todo data for our fake test_user
        todos = [
            {
                "id": uuid.UUID(int=1),
                "title": "1",
                "content": "foo",
                "user_id": fake_user.id,
            },
            {
                "id": uuid.UUID(int=2),
                "title": "2",
                "content": "bar",
                "user_id": fake_user.id,
            },
            {
                "id": uuid.UUID(int=3),
                "title": "3",
                "content": "baz",
                "user_id": fake_user.id,
            },
        ]
        async with db_session() as session:
            for todo in todos:
                await TodoDAO.create(session, todo)
        yield

    async def test_create_todo(self, authed_client: httpx.AsyncClient):
        # User should have no todos to start
        resp = await authed_client.get("/todo")
        assert len(resp.json()) == 0

        data = {"title": "test", "content": "test create todo"}
        resp = await authed_client.post("/todo/", json=data)
        assert resp.json()["title"] == "test"
        assert resp.json()["content"] == "test create todo"

        # Check that user has exactly one todo now
        resp = await authed_client.get("/todo")
        assert len(resp.json()) == 1

    async def test_invalid_create_todo(self, authed_client: httpx.AsyncClient):
        data = {"foo": "bar"}
        resp = await authed_client.post("/todo/", json=data)
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

    async def test_get_all_todos(
        self, authed_client: httpx.AsyncClient, seed_todos: None
    ):
        resp = await authed_client.get("/todo")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_get_todo_by_id(
        self, authed_client: httpx.AsyncClient, seed_todos: None
    ):
        resp = await authed_client.get(f"/todo/{uuid.UUID(int=1)}")
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "1"
        assert js["content"] == "foo"

    async def test_get_todo_by_id_does_not_exist(
        self, authed_client: httpx.AsyncClient
    ):
        resp = await authed_client.get(f"/todo/{uuid.UUID(int=4)}")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Todo not found"}

    async def test_update_todo(
        self, authed_client: httpx.AsyncClient, seed_todos: None
    ):
        endpoint = f"/todo/{uuid.UUID(int=1)}"
        data = {"title": "new title", "content": "new content"}
        # a PUT to /todo/{id} should return the new values
        resp = await authed_client.put(endpoint, json=data)
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "new title"
        assert js["content"] == "new content"

        # a GET to /todo/{id} should also have the new values
        resp = await authed_client.get(endpoint)
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == "00000000-0000-0000-0000-000000000001"
        assert js["title"] == "new title"
        assert js["content"] == "new content"

    async def test_delete_todo(
        self, authed_client: httpx.AsyncClient, seed_todos: None
    ):
        endpoint = f"/todo/{uuid.UUID(int=1)}"
        resp = await authed_client.get(endpoint)
        assert resp.status_code == 200

        # delete the todo
        resp = await authed_client.delete(endpoint)
        assert resp.status_code == 200
        assert resp.json() == {}

        # make sure we get 404 if trying to DELETE again
        resp = await authed_client.delete(endpoint)
        assert resp.status_code == 404

        # and 404 trying to GET it again
        resp = await authed_client.get(endpoint)
        assert resp.status_code == 404
