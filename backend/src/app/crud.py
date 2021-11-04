import uuid
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_user
from app.db import db_session
from app.models import TodoDAO, UserDAO
from app.schemas import TodoCreate, TodoOut, TodoUpdate

router = APIRouter(prefix="/todo", tags=["todo"])


@router.post("/", response_model=TodoOut)
def create_todo(form_data: TodoCreate, user: UserDAO = Depends(get_user)):
    with db_session() as session:
        data = {}
        data.update(form_data)
        data["user"] = user
        new_todo = TodoDAO.create(session, data)
    return new_todo


@router.get("/", response_model=List[TodoOut])
def get_all_todos(user: UserDAO = Depends(get_user)):
    with db_session() as session:
        todos = TodoDAO.get_todos_by_username(session, user.name)
    return todos


@router.get("/{id}", response_model=TodoOut)
def get_todo(id: uuid.UUID, user: UserDAO = Depends(get_user)):
    with db_session() as session:
        todo = TodoDAO.get(session, id)
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Todo not found")
    return todo


@router.put("/{id}", response_model=TodoOut)
def update_todo(
    id: uuid.UUID,
    form_data: TodoUpdate,
    user: UserDAO = Depends(get_user),
):
    with db_session() as session:
        todo = TodoDAO.update_by_id(session, id, **form_data.dict(exclude_unset=True))
        if not todo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.delete("/{id}")
def delete_todo(id: uuid.UUID, user: UserDAO = Depends(get_user)):
    with db_session() as session:
        rowcount = TodoDAO.delete(session, id)
        if rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return {}
