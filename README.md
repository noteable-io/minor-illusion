# Minor Illusion

> You create a sound or an image of an object 
> within range that lasts for the duration.
> 
> If you create an image of an object
> it must be no larger than a 5-foot cube.

*Fun fact: all backend repos at Noteable are named after DnD spells because lead backend engineer @nicholaswold made a joke one time and CTO @MSeal ran with it*

[![backend](https://github.com/noteable-io/minor-illusion/actions/workflows/backend-tests.yaml/badge.svg)](https://github.com/noteable-io/minor-illusion/actions/workflows/backend-tests.yaml) [![Docs](https://github.com/noteable-io/minor-illusion/actions/workflows/publish-docs.yaml/badge.svg)](https://noteable-io.github.io/minor-illusion/)

This is a toy `Todo` application that uses some of the same frameworks and concepts as our production code.  For the Noteable engineering team, this repo can be useful for onboarding, reproducing bugs for external partners, and prototyping systemic changes.  For anyone interested in Noteable, here's a peek into the stack you would be working with:

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

  * Reverse-Proxy:
    * [Traefik](https://traefik.io/) for reverse-proxy and load-balancing between backend instances
  

## Run

Clone this repository and `docker-compose up -d`.  See [Docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/) documentation for installing those services if they aren't already on your development machine.  You can tail the logs for all services with `docker-compose logs -f`.

There are five services that will start up:
    1. A reverse proxy / load-balance web-server (Traefik), transparent to an end user
    2. Frontend (NextJS) UI that you can reach at `http://localhost:5000`
    3. A pair of load-balanced Backend (FastAPI) apps that you can reach at `http://localhost:5000/api`, see `http://localhost:5000/api/docs` for OpenAPI/swagger
    4. CockroachDB that is inacessible from outside of the Docker network
    5. Jupyter Notebook container that you can reach at `http://localhost:8888`, although you'll need to look at `docker-compose logs jupyter` to get the url + access token (something like `http://127.0.0.1:8888/?token=c2a1a877ca8ad47818bd76df917d7aaeca6d8f4a17cb462e`)

*The backend app will not be accessible until after Cockroach DB is online, accepting connections, and has gone through Alembic migrations.  Expect a 30-60 second delay between containers starting and being able to access `http://localhost:5000/api/docs`*

## Docs

See [more documentation](https://noteable-io.github.io/minor-illusion/) created with `mkdocs` and hosted on Github pages, published through Github Actions.