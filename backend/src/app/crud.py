import uuid
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_user
from app.db import db_session
from app.models import Todo, User
from app.schemas import TodoCreate, TodoOut

router = APIRouter(prefix="/todo", tags=["todo"])


@router.get("/", response_model=List[TodoOut])
def get_all_todos(
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    with db_session() as session:
        statement = sa.select(Todo).join(User).where(User.id == User.id)
        results = session.execute(statement)
        todos = results.scalars().all()
    return todos


@router.get("/{id}", response_model=TodoOut)
def get_todo(
    id: uuid.UUID,
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    with db_session() as session:
        statement = sa.select(Todo).where(Todo.id == id)
        results = session.execute(statement)
        todo = results.scalars().one_or_none()
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Todo not found")


@router.put("/{id}", response_model=TodoOut)
def update_todo(
    id: uuid.UUID,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    with db_session() as session:
        statement = sa.select(Todo).where(Todo.id == id)
        results = session.execute(statement)
        todo = results.scalars().one_or_none()
        if not todo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
        if title:
            todo.title = title
        if content:
            todo.content = content
        session.add(todo)
    return todo


@router.delete("/{id}")
def delete_todo(
    id: uuid.UUID,
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    with db_session() as session:
        statement = sa.delete(Todo).where(Todo.id == id)
        results = session.execute(statement)
        if results.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return {}


@router.post("/", response_model=TodoOut)
def add_todo(
    form_data: TodoCreate,
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    new_todo = Todo(user=user, **form_data.dict())
    with db_session() as session:
        session.add(new_todo)
        session.commit()
        session.refresh(new_todo)
    return new_todo
