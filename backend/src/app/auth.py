import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.db import db_session
from app.models import UserDAO

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/login", include_in_schema=False)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with db_session() as session:
        db_user = UserDAO.get_user_by_name(session, form_data.username)
    if not db_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not db_user.password == form_data.password:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Incorrect password")
    return {"access_token": db_user.name, "token_type": "bearer"}


def get_user(token: str = Depends(oauth2_scheme)):
    with db_session() as session:
        db_user = UserDAO.get_user_by_name(session, token)
    if not db_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token/user")
    return db_user
