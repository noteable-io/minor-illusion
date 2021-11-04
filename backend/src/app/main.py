from fastapi import Depends, FastAPI

from app.auth import get_user
from app.auth import router as AuthRouter
from app.crud import router as CrudRouter
from app.models import UserDAO
from app.schemas import UserOut





app = FastAPI()
app.include_router(AuthRouter)
app.include_router(CrudRouter)



@app.get("/me", response_model=UserOut)
def me(user: UserDAO = Depends(get_user)):
    return user
