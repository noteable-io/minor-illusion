# Minor Illusion

> You create a sound or an image of an object 
> within range that lasts for the duration.
> 
> If you create an image of an object
> it must be no larger than a 5-foot cube.

This is a toy `Todo` application that uses some of the same frameworks as our production code.  It might be a good place to explain basic concepts, isolate and reproduce bugs, or use in interviews.  What frameworks do we love at Noteable?

  * Backend:
    * [FastAPI](https://fastapi.tiangolo.com/)
    * [Pydantic](https://pydantic-docs.helpmanual.io/)
    * [SQLAlchemy](https://www.sqlalchemy.org/)
    * [SQLModel](https://sqlmodel.tiangolo.com/)
 
  * Database:
    * [CockroachDB](https://www.cockroachlabs.com/) 

  * Prototyping and exploration:
    * [Jupyter](https://jupyter-docker-stacks.readthedocs.io/en/latest/)


# Run

Clone this repository and `docker-compose up -d`.  It may take a few minutes for the databases to come online.  The backend fastapi app will start once it can connect to the database.  To access Jupyter, watch the logs (`docker-compose logs jupyter`) for the Jupyter url with access token, which will look something like `http://127.0.0.1:8888/?token=a458728e0c549062d578ea9cbaa5ef2d312702c9296363c5`

When the app is up, you can explore its endpoints via OpenAPI/Swagger at `http://localhost:8000/docs`

There are some Notebooks in Jupyter showing how to interact with the database and back-end API, as well as stress test 