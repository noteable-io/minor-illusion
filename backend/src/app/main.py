import os

from app.auth import router as AuthRouter
from app.crud import router as CrudRouter
from app.debug import router as DebugRouter
from app.log_utils import setup_logging
from fastapi import FastAPI

setup_logging()


def build_app() -> FastAPI:
    "Builds the minor-illusion FastAPI application"
    # this is encapsulated in a function to facilitate testing
    if "ROOT_PATH" in os.environ:
        app = FastAPI(root_path=os.environ["ROOT_PATH"])
    else:
        app = FastAPI()
    app.include_router(AuthRouter)
    app.include_router(CrudRouter)
    app.include_router(DebugRouter)
    return app


app = build_app()
