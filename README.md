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

There are several ways to test database interaction in a Python application.  Some common approaches are:  

 - Mock out the database entirely
 - Use an in-memory `sqlite3` database as a stand-in for production
 - Create a test database with your same production stack

We rely heavily on the first option.  One benefit to mocking out the actual database queries is that tests run really fast.  However it does risk missing coverage on critical real-world behavior.  To mock out database interactions, we use a [Data Access Object (DAO)](https://en.wikipedia.org/wiki/Data_access_object) approach towards creating database models.

All interactions with the database are encapsulated in `@classmethod` methods on `DAO` classes.  There are no statements or `session.execute` written in places like `crud.py` or `auth.py`.  By structuring the code this way, we can create `FakeDAO` objects for testing that override those same `@classmethod` and store real sqlalchemy `DAO` objects in memory, just not transacting with a database.

A very brief and incomplete glimpse of what it looks like in practice is below, imports excluded for brevity.  See the relevant files in `backend/src/app` and `backend/src/tests` for more details and comments.

```python
# models.py
class ThingDAO:
    name = sa.Column(sa.String)

    @classmethod
    def get_thing_by_name(cls, session: sa.orm.Session, name: str):
        statement = sa.select(cls).where(cls.name == name)
        results = session.execute(statement)
        thing = results.scalars().one_or_none()
        return thing
```

```python
# schemas.py
class ThingOut(BaseModel):
    name: str
```

```python
# route.py
@app.get('/thing/{name}', response_model=ThingOut)
def get_thing(name: str):
    with db_session() as session:
        thing = ThingDAO.get_thing_by_name(session, name)
    return thing
```

In order to test the route, we would then create a `FakeThingDAO` and patch that in during testing.

```python
# tests/fake_models.py
class FakeThingDAO:
    # CACHE structure is {mock_session: {model.id: model}}
    CACHE = collections.defaultdict(dict)
    dao_cls = ThingDAO

    @classmethod
    def create(cls, mock_session: Mock, model: ThingDAO):
        cls.CACHE[mock_session][model.id] = model
        return model

    @classmethod
    def get_thing_by_name(cls, mock_session: Mock, name: str):
        # equivalent to .where(cls.name==name).one_or_none()
        # cls.CACHE[mock_session].values() is basically the same as a db table
        matches = [item for item in cls.CACHE[mock_session].values() if item.name == name]
        if matches:
            return matches[0]
```

```python
# tests/routes.py
@pytest.fixture(autouse=True)
def patch_route(mocker, db_session):
    mocker.patch('routes.db_session', db_session)
    mocker.patch('routes.ThingDAO', FakeThingDAO)

@pytest.fixture
def make_thing(db_session):
    existing_thing = ThingDAO(name='foo')
    FakeThingDAO.create(db_session, existing_thing)

def test_get_thing(client, make_thing):
    resp = client.get('/thing/foo')
    assert resp.status_code == 200
    assert resp.json() == {'name': 'foo'}
```


### Integration Tests

We use Jupyter Notebooks as one way of testing expected behavior in running applications without any of the mocking that happens in unit tests.  The Jupyter container that gets launched with this repo has the backend code base volume mounted into it, and can also make HTTP calls to the backend application if it's up.  There are Notebooks in `jupyter/notebooks` demonstrating how to pull from the Cockroach DB directly using the backend's SQLAlchemy models as well as "integration test" style Notebooks that hit the REST API.

## Alembic

We use Alembic for database migrations.  The typical development pattern is to edit SQLAlchemy models (`backend/src/app/models.py`) and then [auto-generate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#auto-generating-migrations) new revisions.  It's worth reviewing the [gotchas](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) that come along with `--autogenerate`.

If you want to see how this works in practice, the easiest thing to do is delete everything out of `backend/src/migrations/versions`.  Then bring up the `minor-illusion` app (`docker-compose up --build -d`) and you should observe that there is no table creation or seed data creation by the backend app.  Exec into the backend container (`docker-compose exec backend /bin/bash`) and run `alembic revision --autogenerate -m "test"`. 

Alembic knows about the models in the backend app thanks to a line in `backend/src/migrations/env.py`, `target_metadata = BaseDAO.metadata`  It will compare what those introspected models should look like with what schemas are in Cockroach DB.  Then it will create a revision file in `backend/src/migrations/versions`.  When you run `alembic upgrade head` after that (still in the backend container) then you'll see alembic applying appropriate SQL commands to bring Cockroach DB up to date with the table schemas defined in your `models.py`.