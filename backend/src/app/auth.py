import uuid

from app.db import db_session
from app.models import OrganizationDAO, UserDAO
from app.settings import get_settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY = get_settings().SECRET_KEY
ALGORITHM = "HS256"


class RequestContext:
    def __init__(self, user: UserDAO, org: OrganizationDAO) -> None:
        self.user = user
        self.org = org


@router.post("/login", include_in_schema=False)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    "Authenticate a user and return a JWT token used for further requests"
    async with db_session() as session:
        db_user = await UserDAO.get_user_by_name(session, form_data.username)
    if not db_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not db_user.password == form_data.password:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Incorrect password")
    # delegate token creation partly to make testing easier
    jwt_token = create_token(db_user.id)
    return {"access_token": jwt_token, "token_type": "bearer"}


def create_token(user_id: uuid.UUID):
    "Create a JWT token for the given user_id"
    return jwt.encode({"user_id": str(user_id)}, SECRET_KEY, algorithm=ALGORITHM)


async def get_rctx(token: str = Depends(oauth2_scheme)) -> RequestContext:
    "Return the user for the given JWT token"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    async with db_session() as session:
        user = await UserDAO.get(session, user_id)
        org = user.organization
        if user is None:
            raise credentials_exception
    return RequestContext(user=user, org=org)
