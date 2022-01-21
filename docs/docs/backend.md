# Backend Development

## Poetry

We use `poetry` for dependency management and creating virtual environments.  To add requirements to `minor-illusion`, use `poetry add <package name>`.  If it's a development dependency, such as for testing, include the `--dev` flag.

To set up a development environment on your localhost, navigate to the `backend/src` directory and run `poetry install`.  That should create a `.venv` directory and install all dependencies there.  Afterwards, you can activate that virtual environment with `poetry shell` or use `poetry run`, e.g. `poetry run pytest`.

The same `poetry install` and `.venv` directory creation happens during the `backend` Docker build.  Alembic migrations and the Hypercorn server are both executed with `poetry run` as a prefix.

## Unit Testing

Unit tests are written with `pytest` in the `backend/src/tests` directory.  They can be run on your localhost directly with poetry (`poetry install; poetry run pytest`), or using `tox`.  Alternatively, you can spin up the backend container and run tests in there (`docker-compose run backend tox`).  Lastly, the `tox` tests are run in Github CI/CD during any PR to the `main` branch.

## Database testing

There are several ways to test database interaction in a Python application.  Some common approaches are:

 - Mock out the database entirely
 - Use an in-memory `sqlite3` database as a stand-in for production
 - Maintain a persistent test database alongside the production database

We are able to effectively mock out the database interactions by using a [data access object (DAO)](https://en.wikipedia.org/wiki/Data_access_object) strategy, in which all SQL statement execution is encapsulated in `@classmethod`'s defined in the SQLAlchemy models.  In tests, we can mock those `DAO` classes with `FakeDAO` classes, overriding the appropriate `@classmethod` behavior to return fake data.  This is a good way to test database interactions without actually connecting to a real database.

Additionally, CockroachDB offers an ephemeral in-memory deployment option with the `cockroach demo` command, including enterprise license support for limited time.  In this strategy, a pytest fixture begins running the in-memory cockroach database, creates the tables, and patches the `db_session` to have a connection to the test database instead of production.

## Integration Testing

We use Jupyter Notebooks as one way of testing expected behavior in running applications without any of the mocking that happens in unit tests.  The Jupyter container that gets launched with this repo has the backend code base volume mounted into it, and can also make HTTP calls to the backend application if it's up.  There are Notebooks in `jupyter/notebooks` demonstrating how to pull from the Cockroach DB directly using the backend's SQLAlchemy models as well as "integration test" style Notebooks that hit the REST API.

## Database Migrations

We use Alembic for database migrations.  The typical development pattern is to edit SQLAlchemy models (`backend/src/app/models.py`) and then [auto-generate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#auto-generating-migrations) new revisions.  It's worth reviewing the [gotchas](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) that come along with `--autogenerate`.

If you want to see how this works in practice, the easiest thing to do is delete everything out of `backend/src/migrations/versions`.  Then bring up the `minor-illusion` app (`docker-compose up --build -d`) and you should observe that there is no table creation or seed data creation by the backend app.  Exec into the backend container (`docker-compose exec backend /bin/bash`), activate the virtual environment with `poetry shell`, and run `alembic revision --autogenerate`.

Alembic knows about the models in the backend app thanks to a line in `backend/src/migrations/env.py`, `target_metadata = BaseDAO.metadata`  It will compare what those introspected models should look like with what schemas are in Cockroach DB.  Then it will create a revision file in `backend/src/migrations/versions`.  When you run `alembic upgrade head` after that (still in the backend container) then you'll see alembic applying appropriate SQL commands to bring Cockroach DB up to date with the table schemas defined in your `models.py`.  `alembic downgrade base` will roll back all migrations.