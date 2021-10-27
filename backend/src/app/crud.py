import uuid
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_user
from app.db import db_session
from app.models import Todo, User

router = APIRouter(prefix="/todo", tags=["todo"])


@router.get("/", response_model=List[Todo])
def get_all_todos(
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    with db_session() as session:
        statement = sa.select(Todo).join(User).where(User.id == User.id)
        results = session.execute(statement)
        todos = results.scalars().all()
    return todos


@router.get("/{id}", response_model=Todo)
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


@router.put("/{id}", response_model=Todo)
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
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Todo not found")
        if title:
            todo.title = title
        if content:
            todo.content = content
        session.add(todo)
    return todo


@router.post("/", response_model=Todo)
def add_todo(
    title: str = Form(...),
    content: str = Form(...),
    user: User = Depends(get_user),
    session: Session = Depends(db_session),
):
    todo = Todo(user_id=user.id, title=title, content=content)
    with db_session() as session:
        session.add(todo)
    return todo
