import uuid
from datetime import datetime, timezone
from typing import Union

from app.models import BaseDAO, TodoDAO, UserDAO
from pydantic import BaseModel
from sqlalchemy.orm import Session


class InMemoryMeta(type):
    def __new__(cls, name, bases, dct):
        dao = super().__new__(cls, name, bases, dct)
        dao.CACHE = {}
        return dao


class InMemoryDAO(metaclass=InMemoryMeta):
    CACHE: dict
    dao_cls: BaseDAO

    @classmethod
    def clear(cls):
        cls.CACHE = {}

    @classmethod
    async def new(cls, session: Session, api_model: Union[BaseDAO, BaseModel]):
        if isinstance(api_model, BaseDAO):
            d = api_model.__dict__.copy()
            d.pop("_sa_instance_state")
            api_model = d
        elif isinstance(api_model, BaseModel):
            api_model = api_model.dict(exclude_unset=True)
        api_model.setdefault("id", uuid.uuid4())
        api_model.setdefault("created_at", datetime.now(timezone.utc))

        model = cls.dao_cls(**api_model)
        cls.CACHE[model.id] = model
        return model

    @classmethod
    async def create(cls, session: Session, api_model: Union[BaseDAO, BaseModel]):
        return await cls.new(session, api_model)

    @classmethod
    async def get(cls, session: Session, id: uuid.UUID):
        return cls.CACHE.get(id)

    @classmethod
    async def get_all(cls, session: Session):
        return list(cls.CACHE.values())

    @classmethod
    async def update(
        cls, session: Session, id: uuid.UUID, values: Union[BaseModel, dict]
    ):
        obj = await cls.get(session, id)
        if not obj:
            return None
        if isinstance(values, BaseModel):
            values = values.dict(exclude_unset=True)
        obj.update(values)
        return obj

    @classmethod
    async def delete(cls, session: Session, id: uuid.UUID):
        if id in cls.CACHE:
            del cls.CACHE[id]
            return 1
        else:
            return 0


class FakeUserDAO(InMemoryDAO):
    dao_cls = UserDAO

    @classmethod
    async def get_user_by_name(cls, session: Session, name: str):
        matches = [item for item in cls.CACHE.values() if item.name == name]
        if matches:
            return matches[0]
        else:
            return None


class FakeTodoDAO(InMemoryDAO):
    dao_cls = TodoDAO

    @classmethod
    async def get_todos_by_username(cls, session: Session, name: str):
        return [item for item in cls.CACHE.values() if item.user.name == name]
