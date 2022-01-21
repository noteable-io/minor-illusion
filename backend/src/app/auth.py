from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.db import db_session
from app.models import UserDAO
from app.settings import get_settings

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = get_settings().SECRET_KEY
ALGORITHM = "HS256"


@router.post("/login", include_in_schema=False)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return a JWT token used for further requests."""
    async with db_session() as session:
        db_user = await UserDAO.get_user_by_name(session, form_data.username)
    if not db_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not db_user.password == form_data.password:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Incorrect password")
    # delegate token creation partly to make testing easier
    jwt_token = create_token(db_user.name)
    return {"access_token": jwt_token, "token_type": "bearer"}


def create_token(username: str):
    """Create a JWT token for the given username."""
    return jwt.encode({"user": username}, SECRET_KEY, algorithm=ALGORITHM)


async def get_user(token: str = Depends(oauth2_scheme)):
    """Return the user for the given JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    async with db_session() as session:
        user = await UserDAO.get_user_by_name(session, username)
        if user is None:
            raise credentials_exception
    return user
