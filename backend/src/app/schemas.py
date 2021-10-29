import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    "response_model for User ORM"
    id: uuid.UUID
    created_at: datetime
    name: str

    class Config:
        orm_mode = True


class TodoCreate(BaseModel):
    "Todo form validation for creating new objects"
    title: str
    content: str


class TodoOut(BaseModel):
    "response_model for Todo ORM"
    id: uuid.UUID
    created_at: datetime
    title: str
    content: str

    class Config:
        orm_mode = True
