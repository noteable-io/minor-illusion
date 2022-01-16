import re
import uuid

import httpx
import pytest
from app.models import TodoDAO
from app.schemas import TodoCreate, TodoUpdate


@pytest.mark.asyncio
class TestReadTodos:
    @pytest.mark.usefixtures("auth_seed_user")
    async def test_read(self, client: httpx.AsyncClient, tmp_todo: TodoDAO):
        "tmp_todo is owned by seed user, seed_user should have access"
        endpoint = f"/todo/{tmp_todo.id}"
        resp = await client.get(endpoint)
        assert resp.json()["id"] == str(tmp_todo.id)

    @pytest.mark.xfail(reason="No RBAC implemented in minor-illusion yet")
    @pytest.mark.usefixtures("auth_tmp_user")
    async def test_read_unauth_user(self, client: httpx.AsyncClient, tmp_todo: TodoDAO):
        "tmp_todo is owned by seed user, tmp_user should not have read permissions"
        endpoint = f"/todo/{tmp_todo.id}"
        resp = await client.get(endpoint)
        assert resp.status_code == 401

    @pytest.mark.usefixtures("auth_seed_user")
    async def test_read_invalid_id(self, client: httpx.AsyncClient):
        "Todo with invalid id should not exist"
        endpoint = f"/todo/{uuid.uuid4()}"
        resp = await client.get(endpoint)
        assert resp.status_code == 404

    @pytest.mark.usefixtures("auth_seed_user")
    async def test_read_all_todos(self, client: httpx.AsyncClient, tmp_todo: TodoDAO):
        "Return all todos.  When running in parallel, this could be any number of todos"
        endpoint = "/todo"
        resp = await client.get(endpoint)
        todo_ids = [t["id"] for t in resp.json()]
        assert len(todo_ids) >= 1
        assert str(tmp_todo.id) in todo_ids


@pytest.mark.asyncio
class TestCreateTodos:
    @pytest.mark.usefixtures("auth_seed_user")
    async def test_create(self, client: httpx.AsyncClient):
        endpoint = "/todo"
        body = TodoCreate(title="test title", content="test content")
        resp = await client.post(endpoint, data=body.json())
        assert resp.status_code == 200

        # ensure the data was persisted
        todo_id = resp.json()["id"]
        endpoint = f"/todo/{todo_id}"
        resp = await client.get(endpoint)
        assert resp.status_code == 200
        assert resp.json()["title"] == body.title
        assert resp.json()["content"] == body.content

    # test_create_unauth_user would be next but there's no concept
    # of todo spaces or projects... anyone can create a todo right now

    @pytest.mark.usefixtures("auth_seed_user")
    async def test_create_invalid_params(self, client: httpx.AsyncClient):
        endpoint = "/todo"
        resp = await client.post(endpoint, json={})
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


@pytest.mark.asyncio
class TestUpdateTodos:
    @pytest.mark.usefixtures("auth_seed_user")
    async def test_update(self, client: httpx.AsyncClient, tmp_todo: TodoDAO):
        endpoint = f"/todo/{tmp_todo.id}"
        # First, check that tmp_todo is there and has expected values
        resp = await client.get(endpoint)
        assert resp.status_code == 200
        js = resp.json()
        assert js["title"] == tmp_todo.title
        assert js["content"] == tmp_todo.content

        # Now, update the title and content
        body = TodoUpdate(title="new title", content="new content")
        resp = await client.put(endpoint, data=body.json())
        assert resp.status_code == 200
        js = resp.json()
        assert js["id"] == str(tmp_todo.id)
        assert js["title"] == body.title
        assert js["content"] == body.content

        # Ensure it was persisted
        resp = await client.get(endpoint)
        assert resp.status_code == 200
        js = resp.json()
        assert js["title"] == body.title
        assert js["content"] == body.content

    @pytest.mark.xfail(reason="No RBAC implemented in minor-illusion yet")
    @pytest.mark.usefixtures("auth_tmp_user")
    async def test_update_unauth_user(
        self, client: httpx.AsyncClient, tmp_todo: TodoDAO
    ):
        "tmp_todo is owned by seed user, tmp_user should not have update permissions"
        endpoint = f"/todo/{tmp_todo.id}"
        body = TodoUpdate(title="new title", content="new content")
        resp = await client.put(endpoint, data=body.json())
        assert resp.status_code == 422

    # No test for test_update_invalid_params, updating title and/or content is optional

    @pytest.mark.usefixtures("auth_seed_user")
    async def test_update_invalid_id(self, client: httpx.AsyncClient):
        endpoint = f"/todo/{uuid.uuid4()}"
        body = TodoUpdate(title="new title", content="new content")
        resp = await client.put(endpoint, data=body.json())
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestDeleteTodos:
    @pytest.mark.usefixtures("auth_seed_user")
    async def test_delete(self, client: httpx.AsyncClient, tmp_todo: TodoDAO):
        endpoint = f"/todo/{tmp_todo.id}"
        resp = await client.delete(endpoint)
        assert resp.status_code == 200

        # Ensure it was deleted
        resp = await client.get(endpoint)
        assert resp.status_code == 404

    @pytest.mark.xfail(reason="No RBAC implemented in minor-illusion yet")
    @pytest.mark.usefixtures("auth_tmp_user")
    async def test_delete_unauth_user(
        self, client: httpx.AsyncClient, tmp_todo: TodoDAO
    ):
        "tmp_todo is owned by seed user, tmp_user should not have delete permissions"
        endpoint = f"/todo/{tmp_todo.id}"
        resp = await client.delete(endpoint)
        assert resp.status_code == 422

    @pytest.mark.usefixtures("auth_seed_user")
    async def test_delete_invalid_id(self, client: httpx.AsyncClient):
        endpoint = f"/todo/{uuid.uuid4()}"
        resp = await client.delete(endpoint)
        assert resp.status_code == 404
