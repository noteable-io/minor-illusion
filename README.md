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
    * [SQLModel](https://sqlmodel.tiangolo.com/) (in development) for Pydantic + SQLAlchemy convergence!
    * [Pytest](https://docs.pytest.org/) for testing
    * [Structlog](https://www.structlog.org/en/stable/) for logging

  * Backend prod tools not shown here (yet?):
    * [alembic](https://alembic.sqlalchemy.org/en/latest/) for database migration
    * [tox](https://tox.wiki/en/latest/index.html) for complex testing
    
  * Database:
    * [CockroachDB](https://www.cockroachlabs.com/) 

  * Prototyping, exploration, and integration tests:
    * [Jupyter](https://jupyter-docker-stacks.readthedocs.io/en/latest/)

  * Frontend:
    * [Next.js](https://nextjs.org/)
  

# Run

Clone this repository and `docker-compose up -d`.  It may take a few minutes for the database to come online.  The backend fastapi app will start once it can connect to the database.  To access Jupyter, watch the logs (`docker-compose logs jupyter`) for the Jupyter url with access token, which will look something like `http://127.0.0.1:8888/?token=a458728e0c549062d578ea9cbaa5ef2d312702c9296363c5`

When the app is up, you can explore its endpoints via OpenAPI/Swagger at `http://localhost:8000/docs`

There are some Notebooks in Jupyter showing how to interact with the database and back-end API, as well as stress test 

# Test Backend

`docker-compose run backend python -m pytest`