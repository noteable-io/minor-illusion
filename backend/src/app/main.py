import os

from fastapi import Depends, FastAPI

from app.auth import get_user
from app.auth import router as AuthRouter
from app.crud import router as CrudRouter
from app.log_utils import setup_logging
from app.models import UserDAO
from app.rtu import router as RtuRouter
from app.schemas import UserOut
from app.settings import get_settings

setup_logging()


def build_app() -> FastAPI:
    "Builds the minor-illusion FastAPI application"
    # this is encapsulated in a function to assist with testing
    app = FastAPI(root_path=get_settings().ROOT_PATH)
    app.include_router(AuthRouter)
    app.include_router(CrudRouter)
    app.include_router(RtuRouter)
    return app


app = build_app()


@app.get("/me", response_model=UserOut)
def me(user: UserDAO = Depends(get_user)):
    return user


# Useful for seeing which backend your browser is connected to
# when multiple backends are running behind load-balancer.
@app.get("/host")
def environ():
    return os.environ.get("HOSTNAME")
