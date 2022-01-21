import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_user
from app.db import db_session
from app.models import TodoDAO, UserDAO
from app.schemas import TodoCreate, TodoOut, TodoUpdate

router = APIRouter(prefix="/todo", tags=["todo"])


@router.post("/", response_model=TodoOut)
async def create_todo(form_data: TodoCreate, user: UserDAO = Depends(get_user)):
    async with db_session() as session:
        data = {}
        data.update(form_data)
        data["user"] = user
        new_todo = await TodoDAO.create(session, data)
    return new_todo


@router.get("/", response_model=List[TodoOut])
async def get_all_todos(user: UserDAO = Depends(get_user)):
    async with db_session() as session:
        todos = await TodoDAO.get_todos_by_username(session, user.name)
    return todos


@router.get("/{id}", response_model=TodoOut)
async def get_todo(id: uuid.UUID, user: UserDAO = Depends(get_user)):
    async with db_session() as session:
        todo = await TodoDAO.get(session, id)
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.put("/{id}", response_model=TodoOut)
async def update_todo(
    id: uuid.UUID,
    form_data: TodoUpdate,
    user: UserDAO = Depends(get_user),
):
    async with db_session() as session:
        todo = await TodoDAO.get(session, id)
        if not todo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
        todo.update(form_data)
    return todo


@router.delete("/{id}")
async def delete_todo(id: uuid.UUID, user: UserDAO = Depends(get_user)):
    async with db_session() as session:
        rowcount = await TodoDAO.delete(session, id)
        if rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return {}
