# Minor Illusion

> You create a sound or an image of an object 
> within range that lasts for the duration.
> 
> If you create an image of an object
> it must be no larger than a 5-foot cube.

*Fun fact: all backend repos at Noteable are named after DnD spells because lead backend engineer @nicholaswold made a joke one time and CTO @MSeal ran with it*


This is a toy `Todo` application that uses some of the same frameworks as our production code.  For the Noteable engineering team, it may be useful for demonstrating fundamental concepts, onboarding, or reproducing minimal errors.  It's worth noting that DevOps is not represented here, this repo uses `docker-compose` for convenience over standing up a local kubernetes cluster.  For anyone interested in Noteable, here's a peek into the stack you would be working with:

  * Backend:
    * [Hypercorn](https://pgjones.gitlab.io/hypercorn/) for [ASGI](https://asgi.readthedocs.io/en/latest/)
    * [FastAPI](https://fastapi.tiangolo.com/) for web framework
    * [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
    * [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
    * [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migration
    * [SQLModel](https://sqlmodel.tiangolo.com/) (in development) for Pydantic + SQLAlchemy convergence!
    * [Pytest](https://docs.pytest.org/) for testing
    * [Structlog](https://www.structlog.org/en/stable/) for logging

  * Backend prod tools not shown here (yet?):
    * [tox](https://tox.wiki/en/latest/index.html) for complex testing
    
  * Database:
    * [CockroachDB](https://www.cockroachlabs.com/) 

  * Prototyping, exploration, and integration tests:
    * [Jupyter](https://jupyter-docker-stacks.readthedocs.io/en/latest/)

  * Frontend:
    * [Next.js](https://nextjs.org/)
  

# Run

Clone this repository and `docker-compose up -d`.  See [Docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/) documentation for installing those services if they aren't already on your development machine.  You can tail the logs for all services with `docker-compose logs -f`.

There are four services that will start up:
    1. Frontend (NextJS) UI that you can reach at `http://localhost:3000`
    2. Backend (FastAPI) app that you can reach at `http://localhost:8000`, see `http://localhost:8000/docs` for OpenAPI/swagger
    3. CockroachDB that is inacessible from outside of the Docker network
    4. Jupyter Notebook container that you can reach at `http://localhost:8888`, although you'll need to look at `docker-compose logs jupyter` to get the url + access token (something like `http://127.0.0.1:8888/?token=c2a1a877ca8ad47818bd76df917d7aaeca6d8f4a17cb462e`)

*The Backend app will not be accessible until after Cockroach DB is online, accepting connections, and has gone through Alembic migrations.  Expect a 30-60 second delay between containers starting and being able to access `http://localhost:8000/docs`*


# Developer Experience

## Backend testing

### Unit Tests

We use `pytest` for unit testing.  You can run the tests by exec'ing into the backend container once it's up (`docker-compose exec backend /bin/bash`) and running `python -m pytest`.  Alternatively, from your host machine you can use `docker-compose run backend python -m pytest`.

```
kafonek@DESKTOP-0MLN0FF:~/minor-illusion$ dc run backend python -m pytest
Creating minor-illusion_backend_run ... done
====================================================== test session starts ======================================================
platform linux -- Python 3.9.7, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /usr/src
plugins: mock-3.6.1, anyio-3.3.4
collected 10 items                                                                                                              

tests/test_auth.py ...                                                                                                    [ 30%]
tests/test_crud.py .......                                                                                                [100%]

====================================================== 10 passed in 0.24s =======================================================
```

#### Database Mocking

We use a [Data Access Object (DAO)](https://en.wikipedia.org/wiki/Data_access_object) approach towards creating database models, only querying them through `@classmethod` decorators, in order to easily mock them in testing.  Entirely mocking away database transactions definitely has its shortcomings. One alternative approach is creating an in-memory `sqlite3` database for tests, which may have compatibility differences with Cockroach DB.  Another would be to just stand up a test Cockroach DB instance, although that could add significant latency to running tests.  

What does it mean in practice?  Instead of writing `statement = sa.select(...); results = session.execute(statement)` code in CRUD routers, every query action is represented in `models.py` as part of a `DAO` object.  Router code uses syntax like:

```python
# imaginary crud.py router file
@app.get('/endpoint/{id}', response_model=ThingOut)
def endpoint(id: int):
    with db_session() as session:
        item = ThingDAO.get(session, id)
    return item
```    

instead of:

```python
# imaginary crud.py router file
@app.get('/endpoint/{id}', response_model=ThingOut)
def endpoint(id: int):
    with db_session() as session:
        statement = sa.select(ThingDAO).where(ThingDAO.id == id)
        results = session.execute(statement)
        item = results.scalars().first()
    return item
```

To test the endpoint, you'd have to create a `FakeThingDAO` in tests (see `backend/src/tests/fake_models` for examples), and then patch it into your test.  The `FakeDAO` objects use in-memory dictionaries to represent the actual database tables, and any `@classmethod`'s in your actual `DAO` models will need to be re-implemented in the `FakeDAO`'s to mimic the database transaction behavior.

```python
# imaginary test_crud.py test file
import pytest
from unittest.mock import patch
from .fake_models import FakeThingDAO

@pytest.fixture(autouse=True)
def patch_thing_dao():
    with patch("app.crud.ThingDAO", FakeThingDAO):
        yield

def test_get_endpoint(client):
    resp = client.get('/endpoint/1')
    # ^^ since ThingDAO.get is patched to FakeThingDAO.get, 
    # there is no database transaction.  It's an in-memory
    # FakeThingDAO.CACHE.get(1) which returns a ThingDAO object
    # and that can get rendered into a Pydantic validated json response
    assert resp.status_code == 200
    assert resp.json() = {...}
```


### Integration Tests

We use Jupyter Notebooks as one way of testing expected behavior in running applications without any of the mocking that happens in unit tests.  The Jupyter container that gets launched with this repo has the backend code base volume mounted into it, and can also make HTTP calls to the backend application if it's up.  There are Notebooks in `jupyter/notebooks` demonstrating how to pull from the Cockroach DB directly using the backend's SQLAlchemy models as well as "integration test" style Notebooks that hit the REST API.

## Alembic

We use Alembic for database migrations.  The typical development pattern is to edit SQLAlchemy models (`backend/src/app/models.py`) and then [auto-generate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#auto-generating-migrations) new revisions.  It's worth reviewing the [gotchas](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) that come along with `--autogenerate`.

If you want to see how this works in practice, the easiest thing to do is delete everything out of `backend/src/migrations/versions`.  Then bring up the `minor-illusion` app (`docker-compose up --build -d`) and you should observe that there is no table creation or seed data creation by the backend app.  Exec into the backend container (`docker-compose exec backend /bin/bash`) and run `alembic revision --autogenerate -m "test"`. 

Alembic knows about the models in the backend app thanks to a line in `backend/src/migrations/env.py`, `target_metadata = BaseDAO.metadata`  It will compare what those introspected models should look like with what schemas are in Cockroach DB.  Then it will create a revision file in `backend/src/migrations/versions`.  When you run `alembic upgrade head` after that (still in the backend container) then you'll see alembic applying appropriate SQL commands to bring Cockroach DB up to date with the table schemas defined in your `models.py`.