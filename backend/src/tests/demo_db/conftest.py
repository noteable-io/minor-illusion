import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
import mirakuru
import pytest
from app.main import app
from app.models import BaseDAO, UserDAO
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# shell command to launch ephemeral in-memory cockroach db
COCKROACH_CMD = """cockroach demo --sql-port 26259 --no-example-database -e 'ALTER USER demo with password "noteable";select pg_sleep(1000)'"""

# these should match with the COCKROACH_CMD values
TEST_DB_USER = "demo"
TEST_DB_PASS = "noteable"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = "26259"
TEST_DB_NAME = "defaultdb"

# TOC for this file:
#   1. Override pytest-asyncio event_loop fixture to be session scoped
#   2. Set up an async engine and db_session that will do SAVEPOINT restorations per test
#   3. Fixture for creating a seed test user
#   4. Fixture for creating an httpx.AsyncClient and client that is authorized as test user
#   5. Fixture to start an in-memory cockroach db and create the tables
#
# Of those, only #5 is run automatically.
# The rest are explicitly called as fixture arguments in tests

# 1. override pytest-asyncio event_loop
# If this isn't done, then tests will show errors like "another operation is in progress"
# or "attached to a different loop"
@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


# 2. Set up async engine and db_session
# The engine handles the SAVEPOINT and ROLLBACK
# Sessions inside a .begin_nested() block that try to .commit()
# produce RELEASE SAVEPOINT rather than COMMIT statements

ASYNC_TEST_DB_URL = f"cockroachdb+asyncpg://{TEST_DB_USER}:{TEST_DB_PASS}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
async_engine = create_async_engine(ASYNC_TEST_DB_URL)


@pytest.fixture
async def engine():
    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        yield conn
        await conn.rollback()


@pytest.fixture
async def db_session(engine):
    # Need to put this async context manager definition inside the fixture
    # in order to have access to the engine
    # If we passed db_session into functions as FastAPI dependency injection
    # then this would look different (and probably cleaner)
    @asynccontextmanager
    async def test_db_session() -> AsyncIterator[AsyncSession]:
        Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        session = Session()
        try:
            yield session
            await session.commit()
        finally:
            await session.close()

    yield test_db_session


# 3. Fixture for creating a seed test user
@pytest.fixture
async def fake_user(db_session: AsyncIterator[AsyncSession]):
    "Fixture for creating a seed test user"
    user_data = {"name": "test_user", "password": "pass"}
    async with db_session() as session:
        user = await UserDAO.create(session, user_data)
    yield user


# 4. httpx.AsyncClient and a second version that has the Authorization header
# already set up to be logged in as the test user
@pytest.fixture
async def client():
    "Fixture to return an HTTP client for the fastapi app"
    async with httpx.AsyncClient(
        app=app, base_url="http://test", follow_redirects=True
    ) as client:
        yield client


@pytest.fixture
async def authed_client(client: httpx.AsyncClient, fake_user: UserDAO):
    """
    Fixture to create an HTTP client that includes
    the Authorization header to authenticate against
    FastAPI endpoints, using the "test_user" credentials
    """
    auth_header = {"Authorization": f"bearer {fake_user.name}"}
    client.headers.update(auth_header)
    yield client


# 5. Start in-memory cockroach database and create the tables
# mirakuru is a library that can start processes and give you ways to tell when they are up
SYNC_TEST_DB_URL = f"cockroachdb://{TEST_DB_USER}:{TEST_DB_PASS}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}?sslmode=require"
sync_engine = create_engine(SYNC_TEST_DB_URL)


@pytest.fixture(scope="session")
def manage_cockroach():
    print("in manage_cockroach")
    with mirakuru.TCPExecutor(
        COCKROACH_CMD, host=TEST_DB_HOST, port=int(TEST_DB_PORT)
    ) as process:
        assert process.running()
        print("Cockroach is running according to mirakuru.TCPExecutor")
        yield
    process.stop()


@pytest.fixture(scope="session", autouse=True)
def create_tables(manage_cockroach):
    # Even though the mirakuru TCPExecutor shows that it can send packets to
    # localhost:26259, it will say that demo/noteable is an invalid password
    # I think because we're beating a race condition on executing ALTER USER demo with password
    # so retry a few times here.  Typically it works after 5 tries (.5 seconds)
    # TODO: PR mirakuru to have a PostgresExecutor ?
    tries = 50
    for i in range(tries):
        try:
            BaseDAO.metadata.create_all(sync_engine)
            break
        except:
            print(f"retrying connection (#{i})")
            time.sleep(0.1)
    else:
        print(f"Couldn't create tables after {tries} tries ({tries * 0.1} seconds)")
