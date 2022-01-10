# Live-DB-Testing

The primary difference between tests in this directory and those in `tests/fake_daos` is that the latter mocks out all database transactions using `FakeDAO` classes that store data in memory instead of talking to a real database.  There is a considerable amount of additional mocking that builds upon the `FakeDAO` paradigm.  One goal of this test suite is to reduce cognitive load when reading or writing tests by minimizing or eliminating the use of mocks.  A second benefit is that the tests will more accurately reflect the behavior of the application.

There can be many sources of "magic" between pytest fixtures (especially `autouse=True`), mocking, monkeypatching, and FastAPI dependency injection overrides.  At present, there are:
 - *no* mocking or patching
 - *no* monkeypatching
 - *one* FastAPI dependency injection override, for handling user authentication
 - *two* effective autouse fixtures
   - Start or connect to a CockroachDB, and ensure schema is up to date
   - Override `minor-illusion` `Settings` with test database connection details

## conftest.py

There is a table of contents in the docstring at the top of `conftest.py`, to help make sense of the fixtures available when reading or writing tests.  The first four sections are what will be commonly seen in test files.

 - One-time-creation seed data in Cockroach which should be treated as read-only
 - Per-test-creation temporary data in Cockroach used for reading / editing / deleting
 - `httpx.AsyncClient` test client to make REST requests to `minor-illusion`
 - Authentication options to make requests as the `seed_data.user` or `tmp_user`

## Test Client

The `client` fixture yields an `httpx.AsyncClient` that has the `minor-illusion` FastAPI app passed into it, and an `Authorization` header set so that it gets around the initial HTTP Bearer challenge.

External docs:
 - [FastAPI Async tests](https://fastapi.tiangolo.com/advanced/async-tests/#httpx)
 - [httpx Async support](https://www.python-httpx.org/async/)

## Authentication

`minor-illusion` handles user authentication with the `app.auth.get_user` dependency injection.  All requests to authenticated endpoints expect an Authorization bearer token that is valid JWT.  The `get_user` function validates the JWT, extracts the user, and queries the database to return a `UserDAO` object of the user making the request.

In testing, we override the `get_user` dependency injection to return either the `seed_data.user` or `tmp_user`.  Decorate your test function with one of the following:

 - `@pytest.mark.usefixtures('auth_seed_user')`
 - `@pytest.mark.usefixtures('auth_tmp_user')`

In cases where you need to make multiple requests in the same test, switching who is authenticated on each request, there is an `auth_as` context manager you can use.
External docs:
 - [FastAPI override dependencies in testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

## Seed Data

Using the `seed_data` fixture yields you a `SeedData` dataclass with one attribute: `seed_data.user`.  At the moment there are no endpoints where this is required to be used.  The seed data is created once (session scope) and should be treated as READ ONLY.  Do not edit or delete the seed data in your tests.

## Temporary Data

There are two `tmp_*` fixtures that are designed to be used in `Read`, `Update`, and `Delete` CRUD tests.  They are created per-test (function scope) and deleted when the test completes.
 - `tmp_user` -> `UserDAO`
 - `tmp_todo` -> `TodoDAO` that was created by `seed_data.user`

## Tips for writing tests

 - Type hint your fixtures to make it easier to read the tests, and so developers can easily click into those objects definitions from their IDE
 - When testing CREATE, UPDATE, and DELETE operations, make a follow on READ to ensure changes were persisted
 - When testing CREATE and UPDATE operations, or anything that takes a body, use the Pydantic validation classes that the route uses
   - This gives easy click-through documentation to other developers about what all the options are for that POST/PUT/PATCH

## Testing CRUD routes

Many of the router files define Create-Read-Update-Delete (CRUD) behavior for a given resource.  A test file for a CRUD route should be stuctured something like the following, give or take special use-cases for the specific resource.

- class TestReadThings
    - def test_read()
    - def test_read_unauth_user()
    - def test_read_invalid_id()

- class TestCreateThings
    - def test_create()
    - def test_create_unauth_user()
    - def test_create_invalid_params()

- class TestUpdateThings
    - def test_update()
    - def test_update_unauth_user()
    - def test_update_invalid_params()
    - def test_update_invalid_id()

- class TestDeleteThings
    - def test_delete()
    - def test_delete_unauth_user()
    - def test_delete_invalid_id()
