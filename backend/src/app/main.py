import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI

from app.auth import get_user
from app.auth import router as AuthRouter
from app.crud import router as CrudRouter
from app.db import db_session, engine
from app.models import Base, Todo, User


def init_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


app = FastAPI()
app.include_router(AuthRouter)
app.include_router(CrudRouter)


@app.on_event("startup")
def on_startup():
    while True:
        try:
            init_db()
            break
        except:
            print("Database not responding yet")
            time.sleep(5)

    # Seed data
    user1 = User(name="user1", password="pass")
    user2 = User(name="user2", password="pass")
    users = [user1, user2]
    todos = [
        Todo(user=user1, title="Note 1", content="My first Note"),
        Todo(user=user1, title="Note 2", content="Edit this Note"),
        Todo(
            user=user1,
            title="Note 3",
            content="So many Notes",
        ),
        Todo(user=user1, title="Note 4", content="Reminder: make more Notes"),
    ]
    with db_session() as session:
        session.add_all(users)
        session.add_all(todos)


@app.get("/me", response_model=User, response_model_exclude={"password": ...})
def me(user: User = Depends(get_user)):
    return user
