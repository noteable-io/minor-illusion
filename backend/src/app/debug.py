import os

from fastapi import APIRouter, Depends

from app.auth import RequestContext, get_rctx
from app.models import UserDAO
from app.schemas import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
def me(rctx: RequestContext = Depends(get_rctx)):
    return rctx.user


# Useful for seeing which backend your browser is connected to
# when multiple backends are running behind load-balancer.
@router.get("/host")
def environ():
    return os.environ.get("HOSTNAME")
