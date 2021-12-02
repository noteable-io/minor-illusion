import time
from contextlib import asynccontextmanager

import httpx
import mirakuru
import pytest
from app.main import app
from app.models import BaseDAO, UserDAO
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

SYNC_TEST_DB_URL = (
    "cockroachdb://demo:noteable@localhost:26259/defaultdb?sslmode=require"
)
ASYNC_TEST_DB_URL = "cockroachdb+asyncpg://demo:noteable@localhost:26259/defaultdb"

sync_engine = create_engine(SYNC_TEST_DB_URL)
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
    @asynccontextmanager
    async def test_db_session():
        Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        session = Session()
        try:
            yield session
            await session.commit()
        finally:
            await session.close()

    yield test_db_session


@pytest.fixture
async def fake_user(db_session: AsyncSession):
    "Fixture for creating a seed test user"
    user_data = {"name": "test_user", "password": "pass"}
    async with db_session() as session:
        user = await UserDAO.create(session, user_data)
    yield user


@pytest.fixture
async def client():
    "Fixture to return an HTTP client for the fastapi app"
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
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


@pytest.fixture(scope="session")
def manage_cockroach():
    print("in manage_cockroach")
    cmd = """cockroach demo --sql-port 26259 --no-example-database -e 'ALTER USER demo with password "noteable";select pg_sleep(1000)'"""
    with mirakuru.TCPExecutor(cmd, host="localhost", port=26259) as process:
        assert process.running()
        print("Cockroach is running")
        yield
    process.stop()


@pytest.fixture(scope="session", autouse=True)
def create_tables(manage_cockroach):
    # Even though the mirakuru TCPExecutor shows that it can send packets to
    # localhost:26259, it will say that demo/noteable is an invalid password
    # I think because we're beating a race condition on executing ALTER USER demo with password
    # so retry a few times here..
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
