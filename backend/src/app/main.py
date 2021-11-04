import logging
import time

import structlog
from fastapi import Depends, FastAPI

from app.auth import get_user
from app.auth import router as AuthRouter
from app.create_seed_data import create_seed_data
from app.crud import router as CrudRouter
from app.db import engine
from app.log_utils import setup_logging
from app.models import BaseDAO, UserDAO
from app.schemas import UserOut


def init_tables():
    BaseDAO.metadata.drop_all(engine)
    BaseDAO.metadata.create_all(engine)


setup_logging()
app = FastAPI()
app.include_router(AuthRouter)
app.include_router(CrudRouter)


@app.on_event("startup")
def db_setup():
    while True:
        try:
            init_tables()
            break
        except Exception as e:
            time.sleep(5)

    create_seed_data()


@app.get("/me", response_model=UserOut)
def me(user: UserDAO = Depends(get_user)):
    return user
