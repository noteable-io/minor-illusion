# Minor-Illusion

[minor-illusion](https://github.com/noteable-io/minor-illusion) is an attempt to create a minimal "Todo" web-app that roughly approximates the stack used in the production [Noteable](https://noteable.io/) application.  The three primary goals of this project are:

1. Demonstrating how various frameworks fit together to assist onboarding new developers at Noteable
2. Offering a place to prototype and experiment with large systemic changes, such as upgrading database interactions to be asynchronous
3. Providing example code style and framework choices to job candidates, and possibly as a tool for exploring concepts during interview sessions

**The stack**

* Backend:
    * [Hypercorn](https://pgjones.gitlab.io/hypercorn/) for the [ASGI](https://asgi.readthedocs.io/en/latest/) server
    * [FastAPI](https://fastapi.tiangolo.com/) for the web framework
    * [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
    * [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
    * [sqlalchemy-cockroachdb](https://github.com/cockroachdb/sqlalchemy-cockroachdb) + [asyncpg](https://magicstack.github.io/asyncpg/current/) for the database driver
    * [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migration
    * [SQLModel](https://sqlmodel.tiangolo.com/) (in development) for Pydantic + SQLAlchemy convergence!
    * [Structlog](https://www.structlog.org/en/stable/) for logging
    * [Poetry](https://python-poetry.org/) for package management
    * [Pytest](https://docs.pytest.org/) for writing tests
    * [tox](https://tox.wiki/en/latest/index.html) for running tests
    
  * Database:
    * [CockroachDB](https://www.cockroachlabs.com/) 

  * Prototyping, exploration, and integration tests:
    * [Jupyter](https://jupyter-docker-stacks.readthedocs.io/en/latest/)

  * Frontend:
    * [Next.js](https://nextjs.org/)

  * Docs:
    * [mkdocs](https://www.mkdocs.org/)
