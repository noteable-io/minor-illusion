import logging
import uuid
from typing import List

import structlog
from app.auth import RequestContext, get_rctx
from app.db import db_session
from app.models import TodoDAO
from app.schemas import TodoCreate, TodoOut, TodoUpdate
from fastapi import APIRouter, Depends, HTTPException, status

vanilla_logger = logging.getLogger(__name__)
logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/todo", tags=["todo"])


@router.post("/", response_model=TodoOut)
async def create_todo(form_data: TodoCreate, rctx: RequestContext = Depends(get_rctx)):
    logger.info("In create_todo", rctx=rctx)
    async with db_session() as session:
        data = {}
        data.update(form_data)
        data["user"] = rctx.user
        new_todo = await TodoDAO.create(session, data)
    return new_todo


@router.get("/", response_model=List[TodoOut])
async def get_all_todos(rctx: RequestContext = Depends(get_rctx)):
    logger.info("in get_all_todos", rctx=rctx)
    vanilla_logger.info("vanilla get_all_todos")
    async with db_session() as session:
        todos = await TodoDAO.get_todos_by_username(session, rctx.user.name)
    return todos


@router.get("/{id}", response_model=TodoOut)
async def get_todo(id: uuid.UUID, rctx: RequestContext = Depends(get_rctx)):
    async with db_session() as session:
        todo = await TodoDAO.get(session, id)
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Todo not found")
    return todo


@router.put("/{id}", response_model=TodoOut)
async def update_todo(
    id: uuid.UUID,
    form_data: TodoUpdate,
    rctx: RequestContext = Depends(get_rctx),
):
    async with db_session() as session:
        todo = await TodoDAO.get(session, id)
        if not todo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
        todo.update(form_data)
    return todo


@router.delete("/{id}")
async def delete_todo(id: uuid.UUID, rctx: RequestContext = Depends(get_rctx)):
    async with db_session() as session:
        rowcount = await TodoDAO.delete(session, id)
        if rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return {}
