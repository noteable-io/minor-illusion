"""Fixtures for use in tests.  This file is laid out in the following order:

  0. Imports

Fixtures directly useful to test authors, and which you'll see in a lot of test files -
 1. Seed data written once to the database, treat as READ ONLY
 2. Fixtures yielding temporary DAO objects for reading, updating, and deleting
 3. Test REST client, an httpx.AsyncClient with the `minor-illusion` app passed into it
 4. User authentication overrides

Fixtures that stand up external services (Cockroach).
Test authors don't need to do anything with these explicitly -
 5. Abstract class for spinning up external services with mirakuru.py
 6. CockroachDB running in-memory

Final touches -
 7. Override `minor-illusion` settings to point to external services (autouse=True)
 8. Create the `minor-illusion` FastAPI app
 9. Bump pytest-asyncio event_loop fixture to session scope
"""

# 0. Imports --------------------------------------------------------------
import abc
import asyncio
import dataclasses
import json
import os
import pathlib
import tempfile
import time
from contextlib import contextmanager
from types import TracebackType
from typing import Callable, ContextManager, List, Optional, Tuple, Type

import faker
import httpx
import mirakuru
import pytest
from fastapi import FastAPI
from filelock import FileLock
from pydantic import BaseModel, Field
from sqlalchemy import create_engine

from app.auth import get_user
from app.db import db_session
from app.main import build_app
from app.models import BaseDAO, TodoDAO, UserDAO
from app.settings import Settings, get_settings


# 1. Seed data written once to the database, treat as READ ONLY ---------------
# In the real Noteable app, there are many types of seed data
# that are useful in tests, beyond a default user.  Think
# Spaces, Projects, Files, etc.
# In minor-illusion, this looks like overkill but it represents
# the way we do things in the complex real app.
#
# Seed data should be treated as READ ONLY.  Do not edit/delete.
@dataclasses.dataclass
class SeedData:
    user: UserDAO


@pytest.fixture(scope="session")
async def seed_data():
    # When running tests in parallel, make sure that
    # seed data uniqueness constraints are not violated.
    pid = os.getpid()

    async with db_session() as session:
        name = f"seedy_{pid}"
        password = faker.Faker().password()
        user_data = {"name": name, "password": password}
        user = await UserDAO.create(session=session, api_model=user_data)
    return SeedData(user=user)


# 2. Temporary data ---------------------------------------------------------
# tmp_data should be used in tests that edit/delete data.
@pytest.fixture
async def tmp_user(worker_id: str) -> UserDAO:
    """UserDAO created and soft deleted between tests."""
    async with db_session() as session:
        user_data = {
            "name": f"tmp_user_{worker_id}",
            "password": faker.Faker().password(),
        }
        user = await UserDAO.create(session=session, api_model=user_data)
    yield user
    async with db_session() as session:
        await UserDAO.delete(session=session, id=user.id)


@pytest.fixture
async def tmp_todo(seed_data: SeedData) -> TodoDAO:
    """TodoDAO created and soft deleted between tests.

    Owned by the seed user.
    """
    async with db_session() as session:
        todo_data = {
            "title": faker.Faker().text(),
            "content": faker.Faker().sentence(),
            "user_id": seed_data.user.id,
        }
        todo = await TodoDAO.create(session=session, api_model=todo_data)
    yield todo
    async with db_session() as session:
        await TodoDAO.delete(session=session, id=todo.id)


# 3. Test REST client -------------------------------------------------------
@pytest.fixture
async def client(app: FastAPI) -> httpx.AsyncClient:
    """Create an async test client for the `minor-illusion` app.

    An authorization header must be present or the app
    will return 403 immediately. Normally that bearer token
    is in JWT format and the get_user function would be
    responsible for validating and decoding the token, as well
    as looking up the user in the database.

    This client will have a dummy authorization bearer header
    and count on tests overriding the get_user dependency injection.
    """
    async with httpx.AsyncClient(
        app=app,
        base_url="http://test",
        follow_redirects=True,
        headers={"Authorization": "bearer test-dummy-value"},
    ) as client:
        yield client


# 4. User authentication overrides ------------------------------------------
# Convenience functions to authenticate as seed_data.user, tmp_user, or
# potentially other users if tests need that flexibility in the future.
# Typically you just need to decorate a test function with
# @pytest.mark.usefixtures('auth_seed_user') or 'auth_tmp_user' as appropriate
AuthContext = Callable[[UserDAO], ContextManager[None]]


@pytest.fixture
def auth_as(app: FastAPI) -> AuthContext:
    @contextmanager
    def _auth_as(user: UserDAO):
        """Authenticate as the given user."""
        current_override = app.dependency_overrides.get(get_user)
        app.dependency_overrides[get_user] = lambda: user
        yield
        app.dependency_overrides[get_user] = current_override

    return _auth_as


@pytest.fixture
def auth_seed_user(auth_as: AuthContext, seed_data: SeedData):
    """Make requests authenticated as the seed user."""
    with auth_as(seed_data.user):
        yield


@pytest.fixture
def auth_tmp_user(auth_as: AuthContext, tmp_user: UserDAO):
    """Make requests authenticated as a tmp_user."""
    with auth_as(tmp_user):
        yield


# 5. External Service Management --------------------------------------------
# A context manager for starting external services with mirakuru.py and returning
# connection details.  Supports running tests in parallel by using a manager/worker
# pattern that ensures the external service is only started once.
#
# The connection details are a Pydantic model specific to the service.
# Alternate option is to use a dataclass here but they're so dang finicky
# about subclassing and serializing to json.
#
# Subclasses should not override sessions, and they are not specific to the service.
# They record which workers are using the service when the tests run in parallel.
class ConnectionDetails(BaseModel):
    sessions: List[str] = Field(default_factory=list)


class ExternalServiceLifecycleManager(abc.ABC):
    """Class helping manage access and lifecycle of an external process service
    over a pytest +possible xdist run.

    pytest-xdist aware architecture pattern inspired by
    https://github.com/pytest-dev/pytest-xdist#making-session-scoped-fixtures-execute-only-once

    When not running in parallel, the state file is not used in any way. A service is stood up,
    connection details returned, and service torn down at the end of the tests.

    When running in parallel however, each worker tries to establish a file lock and
    read the state file. If the connection details are not in the state file already,
    then that worker becomes the manager of the service.

    Workers that are not the manager only need to add their `worker_id` into the state file while
    they are processing tests, and remove their `worker_id` from the state file when complete.

    The single manager xdist worker will be responsible for starting an initializing the service
    in __enter__, and then once its own tests are complete and __exit__ is called,
    determine if any other workers still need it up. The manager will not tear down the service until
    all non-manager workers have removed their `worker_id` from the state file.
    """

    json_state_file_name: str = None
    details_class: Type[ConnectionDetails] = ConnectionDetails

    def __init__(
        self,
        worker_id: str,
        tmp_path_factory: pytest.TempPathFactory,
        unused_tcp_port_factory: Callable[[], int],
    ):
        """
        tmp_path_factory: core pytest fixture, returns temporary directories.
        unused_tcp_port_factory: pytest-asyncio fixture, returns unused TCP ports.
        """
        self.manage_process_lifecycle: bool = None

        self.worker_id = worker_id
        self.unused_tcp_port_factory = unused_tcp_port_factory

        # Need to position our state file in a dir common to all of the xdist
        # workers, but still scoped to be within this test run. Will end
        # up being something like $TMPDIR/pytest-of-<username>/pytest-N/
        root_tmp_dir = tmp_path_factory.getbasetemp().parent

        self.state_file_path = root_tmp_dir / self.json_state_file_name
        self.lock_file_path = pathlib.Path(str(self.state_file_path) + ".lock")

    @abc.abstractmethod
    def _start_service(self) -> Tuple[ConnectionDetails, Optional[mirakuru.Executor]]:
        """Start up the external service using mirakuru and
        self.unused_tcp_port_factory.

        Return the mirakuru handle, plus a Pydantic model describing all the facts
        that a client needs to connect to the running service. In an xdist run,
        all workers who need the service will have their ids written to a shared
        state file, and the service won't be cleaned up until the session list is empty.

        If returned mirakuru_process is None, then this indicates to __exit__
        to not try to kill anything (was external managed running process that
        we perhaps needed to post-initialize within python?)
        """

    def __enter__(self) -> ConnectionDetails:
        if self.worker_id == "master":
            # Not running parallel, aka 'simple town.'
            # Just start up our service, no need for file state management.
            service_details, self.mirakuru_process = self._start_service()

            return service_details

        with FileLock(self.lock_file_path):
            if not self.state_file_path.is_file():
                self.manage_process_lifecycle = True
                service_details, self.mirakuru_process = self._start_service()

                state_file_dict = service_details.dict()

                state_file_dict["sessions"] = []
            else:
                self.manage_process_lifecycle = False
                state_file_dict = json.loads(self.state_file_path.read_text())

                # Prep the service connection details we're going to yield.
                service_details = self.details_class(**state_file_dict)

                # Register this xdist session as a non-manager current user of
                # this service so that the manager won't shut it down before
                # we're done with it.
                service_details.sessions.append(self.worker_id)

            # Manager or not, serialize created or mutated state_file_dict
            # to state_file_path while still holding the lockfile lock.
            self.state_file_path.write_text(service_details.json())

        return service_details

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:

        if self.worker_id == "master":
            # Simple town pt. 2. -- we are the only session. Stop the process if we're
            # managing its lifecycle (see TEST_CRDB_DETAILS branch of CockroachManager::_start_service()
            # for case where we're not).
            if self.mirakuru_process:
                self.mirakuru_process.stop()
            return

        if self.manage_process_lifecycle:
            any_other_users = True  # We assume at first, anyway.

            while True:
                with FileLock(self.lock_file_path):
                    state_file_dict = json.loads(self.state_file_path.read_text())
                    # Only the *other* xdist sessions record their presence in here. Not us.
                    # (can then use an empty-or-not test on this list).
                    any_other_users = bool(len(state_file_dict["sessions"]))

                    if not any_other_users:
                        # Finally, nobody else using it!
                        if self.mirakuru_process:
                            self.mirakuru_process.stop()

                        # Clean up our files.
                        self.state_file_path.unlink()
                        # Implicitly also releases the FileLock!
                        self.lock_file_path.unlink()

                        break  # Blessed freedom. Skips sleep.

                # Lock released, but still looping. There are other sessions still.
                # Try again in a bit!
                time.sleep(0.25)

        else:
            with FileLock(self.lock_file_path):
                # All we need to do is remove ourselves from the current sessions. The manager
                # session is responsible for hanging around until it's 'sessions' is observably
                # empty.
                state_file_dict = json.loads(self.state_file_path.read_text())

                concurrent_sessions = state_file_dict["sessions"]
                assert self.worker_id in concurrent_sessions  # Else __enter__ code done messed up.
                concurrent_sessions.remove(self.worker_id)

                self.state_file_path.write_text(json.dumps(state_file_dict))


# 6. Cockroach DB service manager -------------------------------------------
class CockroachDetails(ConnectionDetails):
    """Class returned by the cockroach() fixture describing how to connect."""

    hostname: str = "localhost"
    port: int = 26257
    username: str = "root"
    password: str = ""
    dbname: str = "defaultdb"

    @property
    def sync_dsn(self) -> str:
        """Project self as a SQLAlchemy synchronous DSN."""
        return f"cockroachdb://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.dbname}"

    @property
    def async_dsn(self) -> str:
        """Project self as a SQLAlchemy asynchronous DSN."""
        return f"cockroachdb+asyncpg://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.dbname}"


class CockroachManager(ExternalServiceLifecycleManager):
    json_state_file_name = "cockroachdb.json"
    details_class = CockroachDetails

    def _start_service(self) -> Tuple[CockroachDetails, Optional[mirakuru.Executor]]:
        """Start an in-memory CockroachDB using mirakuru (unless env var
        TEST_CRDB_DETAILS is set, describing a a process already running).

        Cockroach needs two open ports, one for the sql connection and one for an http
        dashboard that can show debug and query information.

        Always ensures that the `minor-illusion` schema is initialized (even if TEST_CRDB_DETAILS route).
        """
        if "TEST_CRDB_DETAILS" in os.environ:
            # As via gate/scripts/run-test-services.sh
            with open(os.environ["TEST_CRDB_DETAILS"]) as existing_details_file:
                user_provided_details = json.load(existing_details_file)
            details = CockroachDetails(**user_provided_details)
            process = None
        else:
            sql_port = self.unused_tcp_port_factory()
            http_port = self.unused_tcp_port_factory()
            hostname = "localhost"
            username = "root"
            password = ""

            details = CockroachDetails(
                username=username,
                password=password,
                hostname=hostname,
                port=sql_port,
                # defaultdb exists, and 'root' user has superuser privs over it.
                dbname="defaultdb",
            )

            # Run process in platforms tempdir to avoid heap_profiler / subdir from littering cwd
            cockroach_cmd = f"""cockroach start-single-node --insecure --listen-addr  localhost:{sql_port} --http-addr localhost:{http_port} --store=type=mem,size=641mib"""
            process = mirakuru.TCPExecutor(
                cockroach_cmd,
                host=hostname,
                port=int(sql_port),
                shell=True,
                cwd=tempfile.gettempdir(),
            )
            process.start()
            assert process.running()

        self._create_schema(details)

        return details, process

    def _create_schema(self, connection_details: CockroachDetails):
        """Create the table schema (if necessary -- will be a logical noop if
        tables already exist)."""
        BaseDAO.metadata.create_all(create_engine(connection_details.sync_dsn))


@pytest.fixture(scope="session")
def cockroach(
    worker_id: str,
    tmp_path_factory: pytest.TempPathFactory,
    unused_tcp_port_factory: Callable[[], int],
) -> CockroachDetails:
    """Fixture to yield the CockroachDB connection details."""
    with CockroachManager(
        worker_id=worker_id,
        tmp_path_factory=tmp_path_factory,
        unused_tcp_port_factory=unused_tcp_port_factory,
    ) as cockroach_details:
        yield cockroach_details


# 7. Override `minor-illusion` settings -------------------------------------
@pytest.fixture(scope="session", autouse=True)
def override_settings(cockroach: CockroachDetails) -> Settings:
    """Override `minor-illusion` settings with connection details for our
    managed external/test services instead of prod services.

    Takes advantage of get_settings() being lru_cached.
    """
    settings = get_settings()
    settings.DB_DSN = cockroach.async_dsn
    return settings


# 8. Create the `minor-illusion` app ----------------------------------------
@pytest.fixture
async def app() -> FastAPI:
    yield build_app()


# 9. pytest-asyncio event_loop ---------------------------------------------
# This is function scoped in pytest-asyncio, needs to be bumped to session scope
# or we get scope mismatch errors.
@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()
